import xml.etree.ElementTree as ET
import heapq
from datetime import datetime
from collections import defaultdict

# Define the Order class
class Order:
    def __init__(self, order_id, operation, price, volume, timestamp):
        self.order_id = order_id
        self.operation = operation
        self.price = float(price)
        self.volume = int(volume)
        self.timestamp = timestamp

    def __lt__(self, other):
        # For buy orders, higher prices come first, then older orders.
        # For sell orders, lower prices come first, then older orders.
        if self.operation == 'BUY':
            if self.price == other.price:
                return self.timestamp < other.timestamp
            return self.price > other.price
        else:
            if self.price == other.price:
                return self.timestamp < other.timestamp
            return self.price < other.price


# OrderBook class to represent an order book for a particular asset
class OrderBook:
    def __init__(self):
        self.buy_orders = []
        self.sell_orders = []
        self.order_map = {}  # Map of order_id to order object

    def add_order(self, order):
        # Match the order before inserting
        self.match_order(order)
        # Insert to the heap and map if not fully matched
        if order.volume > 0:
            heapq.heappush(self.buy_orders if order.operation == 'BUY' else self.sell_orders, order)
            self.order_map[order.order_id] = order

    def delete_order(self, order_id):
        # Mark the order as deleted in the map
        if order_id in self.order_map:
            self.order_map[order_id].volume = 0
            # del self.order_map[top_order.order_id]

    def match_order(self, new_order):
        opposite_orders = self.sell_orders if new_order.operation == 'BUY' else self.buy_orders
        while opposite_orders and new_order.volume > 0:
            # Peek at the top order
            top_order = opposite_orders[0]

             # Clean up the heap: remove zero-volume orders at the root (lazy deletion)
            if(top_order.volume == 0):
                heapq.heappop(opposite_orders)
                del self.order_map[top_order.order_id]
                continue

            if (new_order.operation == 'BUY' and new_order.price >= top_order.price) or (new_order.operation == 'SELL' and new_order.price <= top_order.price):
                match_volume = min(new_order.volume, top_order.volume)
                new_order.volume -= match_volume
                top_order.volume -= match_volume
                # If top order is fully matched, pop from heap and remove from map
                if top_order.volume == 0:
                    heapq.heappop(opposite_orders)
                    del self.order_map[top_order.order_id]
            else:
                break  # No more matches possible
            

    def __str__(self):

        buy_orders = [order for order in self.buy_orders if order.volume > 0]
        sell_orders = [order for order in self.sell_orders if order.volume > 0]
        
        buy_orders.sort()
        sell_orders.sort()
        # Format the order book for display
        max_length = max(len(buy_orders), len(sell_orders))
        formatted_order_book = []

        for i in range(max_length):
            buy_order = f"{buy_orders[i].volume}@{buy_orders[i].price:.2f}" if i < len(buy_orders) else " " * 8
            sell_order = f"{sell_orders[i].volume}@{sell_orders[i].price:.2f}" if i < len(sell_orders) else ""
            formatted_order_book.append(f"{buy_order} -- {sell_order}")

        return '\n'.join(formatted_order_book)

# Function to process orders from an XML file
def process_orders_xml(xml_file_path):
    order_books = defaultdict(OrderBook)  # Dictionary to hold all order books
    start_time = datetime.now()

    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    timestamp = 0
    for order_msg in root:
        book_name = order_msg.attrib['book']
        order_id = order_msg.attrib['orderId']
        timestamp += 1
        if order_msg.tag == 'AddOrder':
            operation = order_msg.get('operation')
            price = float(order_msg.get('price'))
            volume = int(order_msg.get('volume'))
            order = Order(order_id, operation, price, volume, timestamp)
            order_books[book_name].add_order(order)
        elif order_msg.tag == 'DeleteOrder':
            order_books[book_name].delete_order(order_id)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print out the order books
    print(f"Processing started at: {start_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    for book_name, order_book in order_books.items():
        print(f"Book: {book_name}")
        print("      Buy -- Sell")
        print("========================")
        print(order_book)
        print()
    print(f"Processing completed at: {end_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    print(f"Processing Duration: {duration:.3f} seconds")

    return order_books  # Return the order books for further inspection if needed

# Test the sample XML file
xml_path = "orders 1 (2).xml"
process_orders_xml(xml_path)
