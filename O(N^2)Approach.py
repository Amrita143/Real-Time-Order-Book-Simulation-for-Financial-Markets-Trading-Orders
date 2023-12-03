from collections import defaultdict, deque
from datetime import datetime
import xml.etree.ElementTree as ET
import bisect

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

    def add_order(self, order):
        # Add an order to the buy or sell side after matching
        if order.operation == 'BUY':
            self.match_order(order, self.sell_orders)
            if order.volume > 0:  # if not fully matched, add to book
                bisect.insort_left(self.buy_orders, order)
        else:
            self.match_order(order, self.buy_orders)
            if order.volume > 0:  # if not fully matched, add to book
                bisect.insort_left(self.sell_orders, order)

    def delete_order(self, order_id):
        # Delete an order from the buy or sell side
        orders = self.buy_orders
        for order in orders:
            if order.order_id == order_id:
                orders.remove(order)
                break
        orders = self.sell_orders
        for order in orders:
            if order.order_id == order_id:
                orders.remove(order)
                break


    def match_order(self, new_order, opposite_orders):
        # Match a new order with orders on the opposite side of the book
        while opposite_orders and new_order.volume > 0:
            top_order = opposite_orders[0]
            if ((new_order.operation == 'BUY' and new_order.price >= top_order.price) or
                (new_order.operation == 'SELL' and new_order.price <= top_order.price)):
                # Match volumes
                match_volume = min(new_order.volume, top_order.volume)
                new_order.volume -= match_volume
                top_order.volume -= match_volume
                if top_order.volume == 0:
                    opposite_orders.pop(0)  # Remove the order if fully matched
            else:
                break  # No more matches possible


     
    def __str__(self):
        # Find the longer side to ensure the output has equal length rows
        max_length = max(len(self.buy_orders), len(self.sell_orders))
        formatted_order_book = []

        for i in range(max_length):
            # Get the buy order if available
            if i < len(self.buy_orders):
                buy_order = f"{self.buy_orders[i].volume}@{self.buy_orders[i].price:.2f}"
            else:
                buy_order = " " * 8  # Adjust the number of spaces to align with your output format

            # Get the sell order if available
            if i < len(self.sell_orders):
                sell_order = f"{self.sell_orders[i].volume}@{self.sell_orders[i].price:.2f}"
            else:
                sell_order = ""

            # Combine the buy and sell orders with the separator
            formatted_order_book.append(f"{buy_order} -- {sell_order}")

        return '\n'.join(formatted_order_book)

# Function to process orders from an XML file
def process_orders_xml(xml_file_path):
    order_books = defaultdict(OrderBook)  # Dictionary to hold all order books
    start_time = datetime.now()

    # Parse the XML file
    tree = ET.parse(xml_file_path)
    root = tree.getroot()
    time=0
    for order_msg in root:
        book_name = order_msg.attrib['book']
        order_id = order_msg.attrib['orderId']
        time+=1
        # Process AddOrder
        if order_msg.tag == 'AddOrder':
            operation = order_msg.get('operation')
            price = order_msg.get('price')
            volume = order_msg.get('volume')
            timestamp = time
            order = Order(order_id, operation, price, volume, timestamp)
            order_books[book_name].add_order(order)
        # Process DeleteOrder
        elif order_msg.tag == 'DeleteOrder':
            order_books[book_name].delete_order(order_id)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Print out the order books
    print(f"Processing started at: {start_time.strftime('%Y-%m-%d %H:%M:%S.%f')}")
    for book_name, order_book in order_books.items():
        print(f"book: {book_name}")
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
