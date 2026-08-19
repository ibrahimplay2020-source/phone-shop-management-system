import sqlite3
import os
import customtkinter as ctk
from tkinter import messagebox
from datetime import date

# ====================================
# DATABASE
# ====================================

# Always save the DB in the same folder as this script
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH  = os.path.join(BASE_DIR, "phone_shop.db")

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS Customers(
    customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    phone       TEXT,
    city        TEXT
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Phones(
    phone_id INTEGER PRIMARY KEY AUTOINCREMENT,
    brand    TEXT NOT NULL,
    model    TEXT NOT NULL,
    price    REAL DEFAULT 0,
    stock    INTEGER DEFAULT 0
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS Orders(
    order_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id INTEGER,
    phone_id    INTEGER,
    quantity    INTEGER,
    order_date  TEXT,
    FOREIGN KEY(customer_id) REFERENCES Customers(customer_id),
    FOREIGN KEY(phone_id)    REFERENCES Phones(phone_id)
)
""")

# Add order_date column if upgrading from old DB
try:
    cursor.execute("ALTER TABLE Orders ADD COLUMN order_date TEXT")
except Exception:
    pass

conn.commit()

# ====================================
# HELPERS
# ====================================

def is_positive_int(val):
    try:
        return int(val) >= 0
    except ValueError:
        return False

def is_positive_float(val):
    try:
        return float(val) >= 0
    except ValueError:
        return False

def confirm(msg):
    return messagebox.askyesno("Confirm", msg)

# ====================================
# PHONE FUNCTIONS
# ====================================

def add_phone():
    brand = brand_entry.get().strip()
    model = model_entry.get().strip()
    price = price_entry.get().strip()
    stock = stock_entry.get().strip()

    if not brand or not model:
        messagebox.showerror("Error", "Brand and Model are required")
        return
    if not is_positive_float(price):
        messagebox.showerror("Error", "Price must be a valid positive number")
        return
    if not is_positive_int(stock):
        messagebox.showerror("Error", "Stock must be a valid positive integer")
        return

    cursor.execute("""
        INSERT INTO Phones(brand, model, price, stock)
        VALUES(?, ?, ?, ?)
    """, (brand, model, float(price), int(stock)))
    conn.commit()

    messagebox.showinfo("Success", "Phone Added")
    for e in (brand_entry, model_entry, price_entry, stock_entry):
        e.delete(0, "end")
    show_phones()
    refresh_dashboard()


def show_phones():
    phone_textbox.delete("1.0", "end")
    cursor.execute("SELECT * FROM Phones ORDER BY phone_id")
    for row in cursor.fetchall():
        stock_warn = " ⚠️ LOW" if row[4] <= 2 else ""
        phone_textbox.insert("end",
            f"ID:{row[0]} | {row[1]} {row[2]} | Price:{row[3]:.2f} DA | Stock:{row[4]}{stock_warn}\n"
        )


def delete_phone():
    phone_id = delete_entry.get().strip()
    if not phone_id:
        messagebox.showerror("Error", "Enter a Phone ID")
        return
    cursor.execute("SELECT brand, model FROM Phones WHERE phone_id=?", (phone_id,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Phone ID not found")
        return
    if not confirm(f"Delete {row[0]} {row[1]}? Orders linked to it will also be removed."):
        return
    cursor.execute("DELETE FROM Orders WHERE phone_id=?", (phone_id,))
    cursor.execute("DELETE FROM Phones WHERE phone_id=?", (phone_id,))
    conn.commit()
    messagebox.showinfo("Success", "Phone Deleted")
    delete_entry.delete(0, "end")
    show_phones()
    show_orders()
    refresh_dashboard()


def update_stock():
    phone_id  = update_id_entry.get().strip()
    new_stock = update_stock_entry.get().strip()
    if not phone_id or not new_stock:
        messagebox.showerror("Error", "Fill Phone ID and New Stock")
        return
    if not is_positive_int(new_stock):
        messagebox.showerror("Error", "Stock must be a valid positive integer")
        return
    cursor.execute("SELECT phone_id FROM Phones WHERE phone_id=?", (phone_id,))
    if not cursor.fetchone():
        messagebox.showerror("Error", "Phone ID not found")
        return
    cursor.execute("UPDATE Phones SET stock=? WHERE phone_id=?", (int(new_stock), phone_id))
    conn.commit()
    messagebox.showinfo("Success", "Stock Updated")
    update_id_entry.delete(0, "end")
    update_stock_entry.delete(0, "end")
    show_phones()
    refresh_dashboard()


def edit_phone():
    phone_id  = edit_phone_id_entry.get().strip()
    new_brand = edit_brand_entry.get().strip()
    new_model = edit_model_entry.get().strip()
    new_price = edit_price_entry.get().strip()

    if not phone_id:
        messagebox.showerror("Error", "Enter a Phone ID")
        return
    cursor.execute("SELECT brand, model, price FROM Phones WHERE phone_id=?", (phone_id,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Phone ID not found")
        return

    brand = new_brand if new_brand else row[0]
    model = new_model if new_model else row[1]

    if new_price:
        if not is_positive_float(new_price):
            messagebox.showerror("Error", "Price must be a valid positive number")
            return
        price = float(new_price)
    else:
        price = row[2]

    cursor.execute("""
        UPDATE Phones SET brand=?, model=?, price=? WHERE phone_id=?
    """, (brand, model, price, phone_id))
    conn.commit()
    messagebox.showinfo("Success", "Phone Updated")
    for e in (edit_phone_id_entry, edit_brand_entry, edit_model_entry, edit_price_entry):
        e.delete(0, "end")
    show_phones()
    refresh_dashboard()


def search_phone():
    keyword = search_entry.get().strip()
    phone_textbox.delete("1.0", "end")
    cursor.execute("""
        SELECT * FROM Phones
        WHERE brand LIKE ? OR model LIKE ?
        ORDER BY phone_id
    """, (f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    if not rows:
        phone_textbox.insert("end", "No results found.\n")
        return
    for row in rows:
        stock_warn = " ⚠️ LOW" if row[4] <= 2 else ""
        phone_textbox.insert("end",
            f"ID:{row[0]} | {row[1]} {row[2]} | Price:{row[3]:.2f} DA | Stock:{row[4]}{stock_warn}\n"
        )


# ====================================
# CUSTOMER FUNCTIONS
# ====================================

def add_customer():
    name  = cust_name_entry.get().strip()
    phone = cust_phone_entry.get().strip()
    city  = cust_city_entry.get().strip()

    if not name or not phone or not city:
        messagebox.showerror("Error", "Fill all customer fields")
        return

    cursor.execute("""
        INSERT INTO Customers(name, phone, city)
        VALUES(?, ?, ?)
    """, (name, phone, city))
    conn.commit()
    messagebox.showinfo("Success", "Customer Added")
    for e in (cust_name_entry, cust_phone_entry, cust_city_entry):
        e.delete(0, "end")
    show_customers()
    refresh_dashboard()


def show_customers():
    cust_textbox.delete("1.0", "end")
    cursor.execute("SELECT * FROM Customers ORDER BY customer_id")
    for row in cursor.fetchall():
        cust_textbox.insert("end",
            f"ID:{row[0]} | Name:{row[1]} | Phone:{row[2]} | City:{row[3]}\n"
        )


def delete_customer():
    customer_id = cust_delete_entry.get().strip()
    if not customer_id:
        messagebox.showerror("Error", "Enter a Customer ID")
        return
    cursor.execute("SELECT name FROM Customers WHERE customer_id=?", (customer_id,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Customer ID not found")
        return
    if not confirm(f"Delete customer '{row[0]}'? Their orders will also be removed."):
        return
    cursor.execute("DELETE FROM Orders WHERE customer_id=?", (customer_id,))
    cursor.execute("DELETE FROM Customers WHERE customer_id=?", (customer_id,))
    conn.commit()
    messagebox.showinfo("Success", "Customer Deleted")
    cust_delete_entry.delete(0, "end")
    show_customers()
    show_orders()
    refresh_dashboard()


def edit_customer():
    customer_id = edit_cust_id_entry.get().strip()
    new_name    = edit_cust_name_entry.get().strip()
    new_phone   = edit_cust_phone_entry.get().strip()
    new_city    = edit_cust_city_entry.get().strip()

    if not customer_id:
        messagebox.showerror("Error", "Enter a Customer ID")
        return
    cursor.execute("SELECT name, phone, city FROM Customers WHERE customer_id=?", (customer_id,))
    row = cursor.fetchone()
    if not row:
        messagebox.showerror("Error", "Customer ID not found")
        return

    name  = new_name  if new_name  else row[0]
    phone = new_phone if new_phone else row[1]
    city  = new_city  if new_city  else row[2]

    cursor.execute("""
        UPDATE Customers SET name=?, phone=?, city=? WHERE customer_id=?
    """, (name, phone, city, customer_id))
    conn.commit()
    messagebox.showinfo("Success", "Customer Updated")
    for e in (edit_cust_id_entry, edit_cust_name_entry, edit_cust_phone_entry, edit_cust_city_entry):
        e.delete(0, "end")
    show_customers()


def search_customer():
    keyword = cust_search_entry.get().strip()
    cust_textbox.delete("1.0", "end")
    cursor.execute("""
        SELECT * FROM Customers
        WHERE name LIKE ? OR city LIKE ? OR phone LIKE ?
        ORDER BY customer_id
    """, (f"%{keyword}%", f"%{keyword}%", f"%{keyword}%"))
    rows = cursor.fetchall()
    if not rows:
        cust_textbox.insert("end", "No results found.\n")
        return
    for row in rows:
        cust_textbox.insert("end",
            f"ID:{row[0]} | Name:{row[1]} | Phone:{row[2]} | City:{row[3]}\n"
        )


# ====================================
# ORDER FUNCTIONS
# ====================================

def place_order():
    customer_id = order_cust_id_entry.get().strip()
    phone_id    = order_phone_id_entry.get().strip()
    quantity    = order_qty_entry.get().strip()

    if not customer_id or not phone_id or not quantity:
        messagebox.showerror("Error", "Fill all order fields")
        return
    if not is_positive_int(quantity) or int(quantity) == 0:
        messagebox.showerror("Error", "Quantity must be a positive integer")
        return

    cursor.execute("SELECT name FROM Customers WHERE customer_id=?", (customer_id,))
    if not cursor.fetchone():
        messagebox.showerror("Error", "Customer ID not found")
        return

    cursor.execute("SELECT stock, brand, model FROM Phones WHERE phone_id=?", (phone_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Phone ID not found")
        return

    current_stock, brand, model = result
    qty = int(quantity)
    if qty > current_stock:
        messagebox.showerror("Error", f"Not enough stock for {brand} {model}. Available: {current_stock}")
        return

    today = date.today().isoformat()
    cursor.execute("""
        INSERT INTO Orders(customer_id, phone_id, quantity, order_date)
        VALUES(?, ?, ?, ?)
    """, (customer_id, phone_id, qty, today))
    cursor.execute("UPDATE Phones SET stock = stock - ? WHERE phone_id=?", (qty, phone_id))
    conn.commit()

    messagebox.showinfo("Success", f"Order placed for {brand} {model} x{qty}")
    for e in (order_cust_id_entry, order_phone_id_entry, order_qty_entry):
        e.delete(0, "end")
    show_orders()
    show_phones()
    refresh_dashboard()


def show_orders():
    _display_orders("""
        SELECT o.order_id, c.name, c.city, p.brand, p.model,
               o.quantity, (o.quantity * p.price), o.order_date
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        JOIN Phones    p ON o.phone_id    = p.phone_id
        ORDER BY o.order_id
    """)


def _display_orders(query, params=()):
    order_textbox.delete("1.0", "end")
    cursor.execute(query, params)
    rows = cursor.fetchall()
    if not rows:
        order_textbox.insert("end", "No orders found.\n")
        return
    for row in rows:
        order_date = row[7] if row[7] else "N/A"
        order_textbox.insert("end",
            f"Order#{row[0]} | {order_date} | Customer:{row[1]} ({row[2]}) | "
            f"Phone:{row[3]} {row[4]} x{row[5]} | Total:{row[6]:.2f} DA\n"
        )


def search_order():
    keyword = order_search_entry.get().strip()
    if not keyword:
        show_orders()
        return
    # Try matching order ID directly
    order_textbox.delete("1.0", "end")
    cursor.execute("""
        SELECT o.order_id, c.name, c.city, p.brand, p.model,
               o.quantity, (o.quantity * p.price), o.order_date
        FROM Orders o
        JOIN Customers c ON o.customer_id = c.customer_id
        JOIN Phones    p ON o.phone_id    = p.phone_id
        WHERE CAST(o.order_id AS TEXT) LIKE ?
           OR c.name  LIKE ?
           OR p.brand LIKE ?
           OR p.model LIKE ?
           OR o.order_date LIKE ?
        ORDER BY o.order_id
    """, (f"%{keyword}%",) * 5)
    rows = cursor.fetchall()
    if not rows:
        order_textbox.insert("end", "No orders found.\n")
        return
    for row in rows:
        order_date = row[7] if row[7] else "N/A"
        order_textbox.insert("end",
            f"Order#{row[0]} | {order_date} | Customer:{row[1]} ({row[2]}) | "
            f"Phone:{row[3]} {row[4]} x{row[5]} | Total:{row[6]:.2f} DA\n"
        )


def resequence_orders():
    """Reassign order_id values to fill any gaps, starting from 1."""
    cursor.execute("SELECT order_id FROM Orders ORDER BY order_id")
    rows = cursor.fetchall()
    # Temporarily rename sqlite_sequence to avoid AUTOINCREMENT conflicts
    for new_id, (old_id,) in enumerate(rows, start=1):
        if new_id != old_id:
            cursor.execute("UPDATE Orders SET order_id=? WHERE order_id=?", (new_id, old_id))
    # Reset the AUTOINCREMENT counter to match the current max
    cursor.execute("SELECT MAX(order_id) FROM Orders")
    max_id = cursor.fetchone()[0] or 0
    cursor.execute("UPDATE sqlite_sequence SET seq=? WHERE name='Orders'", (max_id,))
    conn.commit()


def delete_order():
    order_id = del_order_id_entry.get().strip()
    if not order_id:
        messagebox.showerror("Error", "Enter an Order ID")
        return
    cursor.execute("SELECT phone_id, quantity FROM Orders WHERE order_id=?", (order_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Order ID not found")
        return
    if not confirm(f"Delete Order #{order_id}? Stock will be restored."):
        return
    phone_id, quantity = result
    cursor.execute("UPDATE Phones SET stock = stock + ? WHERE phone_id=?", (quantity, phone_id))
    cursor.execute("DELETE FROM Orders WHERE order_id=?", (order_id,))
    conn.commit()
    resequence_orders()
    messagebox.showinfo("Success", "Order Deleted & Stock Restored")
    del_order_id_entry.delete(0, "end")
    show_orders()
    show_phones()
    refresh_dashboard()


def edit_order():
    order_id = edit_order_id_entry.get().strip()
    new_qty  = edit_order_qty_entry.get().strip()

    if not order_id or not new_qty:
        messagebox.showerror("Error", "Fill Order ID and New Quantity")
        return
    if not is_positive_int(new_qty) or int(new_qty) == 0:
        messagebox.showerror("Error", "Quantity must be a positive integer")
        return

    cursor.execute("SELECT phone_id, quantity FROM Orders WHERE order_id=?", (order_id,))
    result = cursor.fetchone()
    if not result:
        messagebox.showerror("Error", "Order ID not found")
        return

    phone_id, old_qty = result
    new_qty = int(new_qty)
    diff    = new_qty - old_qty  # >0 = needs more stock, <0 = frees stock

    cursor.execute("SELECT stock, brand, model FROM Phones WHERE phone_id=?", (phone_id,))
    stock_row = cursor.fetchone()
    current_stock = stock_row[0]

    if diff > current_stock:
        messagebox.showerror("Error", f"Not enough stock for {stock_row[1]} {stock_row[2]}. Available: {current_stock}")
        return

    cursor.execute("UPDATE Orders SET quantity=? WHERE order_id=?", (new_qty, order_id))
    cursor.execute("UPDATE Phones SET stock = stock - ? WHERE phone_id=?", (diff, phone_id))
    conn.commit()
    messagebox.showinfo("Success", "Order Updated")
    edit_order_id_entry.delete(0, "end")
    edit_order_qty_entry.delete(0, "end")
    show_orders()
    show_phones()
    refresh_dashboard()


# ====================================
# DASHBOARD
# ====================================

def refresh_dashboard():
    cursor.execute("SELECT COUNT(*) FROM Customers")
    total_customers = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM Orders")
    total_orders = cursor.fetchone()[0]

    cursor.execute("SELECT SUM(o.quantity * p.price) FROM Orders o JOIN Phones p ON o.phone_id = p.phone_id")
    revenue = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM Phones")
    total_phones = cursor.fetchone()[0]

    cursor.execute("SELECT brand, model, stock FROM Phones WHERE stock <= 2 ORDER BY stock")
    low_stock = cursor.fetchall()

    dash_textbox.delete("1.0", "end")
    dash_textbox.insert("end", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    dash_textbox.insert("end", f"  👤 Total Customers : {total_customers}\n")
    dash_textbox.insert("end", f"  📱 Total Phones    : {total_phones}\n")
    dash_textbox.insert("end", f"  🧾 Total Orders    : {total_orders}\n")
    dash_textbox.insert("end", f"  💰 Total Revenue   : {revenue:,.2f} DA\n")
    dash_textbox.insert("end", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
    if low_stock:
        dash_textbox.insert("end", "  ⚠️  LOW STOCK ALERT:\n")
        for item in low_stock:
            dash_textbox.insert("end", f"     • {item[0]} {item[1]} — only {item[2]} left\n")
    else:
        dash_textbox.insert("end", "  ✅ All phones have sufficient stock\n")
    dash_textbox.insert("end", "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")


# ====================================
# GUI
# ====================================

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.title("Phone Shop Management")
app.geometry("980x880")

ctk.CTkLabel(
    app,
    text="📱 PHONE SHOP MANAGEMENT SYSTEM",
    font=("Arial", 22, "bold")
).pack(pady=12)

tabview = ctk.CTkTabview(app, width=940, height=800)
tabview.pack(padx=20, pady=5, fill="both", expand=True)

tab_dashboard = tabview.add("📊 Dashboard")
tab_phones    = tabview.add("📱 Phones")
tab_customers = tabview.add("👤 Customers")
tab_orders    = tabview.add("🧾 Orders")

# ====================================
# DASHBOARD TAB
# ====================================

ctk.CTkLabel(tab_dashboard, text="Overview", font=("Arial", 16, "bold")).pack(pady=(12, 4))

ctk.CTkButton(tab_dashboard, text="🔄 Refresh Dashboard", command=refresh_dashboard).pack(pady=6)

dash_textbox = ctk.CTkTextbox(tab_dashboard, width=860, height=400, font=("Courier", 14))
dash_textbox.pack(pady=10, padx=10)

# ====================================
# PHONES TAB
# ====================================

# --- Add Phone ---
frame_add = ctk.CTkFrame(tab_phones)
frame_add.pack(pady=8, padx=10, fill="x")
ctk.CTkLabel(frame_add, text="Add Phone", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=5, pady=(8,4))

brand_entry = ctk.CTkEntry(frame_add, placeholder_text="Brand", width=140)
brand_entry.grid(row=1, column=0, padx=5, pady=5)

model_entry = ctk.CTkEntry(frame_add, placeholder_text="Model", width=140)
model_entry.grid(row=1, column=1, padx=5, pady=5)

price_entry = ctk.CTkEntry(frame_add, placeholder_text="Price (DA)", width=120)
price_entry.grid(row=1, column=2, padx=5, pady=5)

stock_entry = ctk.CTkEntry(frame_add, placeholder_text="Stock", width=100)
stock_entry.grid(row=1, column=3, padx=5, pady=5)

ctk.CTkButton(frame_add, text="➕ Add", command=add_phone).grid(row=1, column=4, padx=5)

# --- Edit Phone ---
frame_edit_phone = ctk.CTkFrame(tab_phones)
frame_edit_phone.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_edit_phone, text="Edit Phone", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=5, pady=(8,4))

edit_phone_id_entry = ctk.CTkEntry(frame_edit_phone, placeholder_text="Phone ID", width=100)
edit_phone_id_entry.grid(row=1, column=0, padx=5, pady=5)

edit_brand_entry = ctk.CTkEntry(frame_edit_phone, placeholder_text="New Brand", width=130)
edit_brand_entry.grid(row=1, column=1, padx=5, pady=5)

edit_model_entry = ctk.CTkEntry(frame_edit_phone, placeholder_text="New Model", width=130)
edit_model_entry.grid(row=1, column=2, padx=5, pady=5)

edit_price_entry = ctk.CTkEntry(frame_edit_phone, placeholder_text="New Price", width=120)
edit_price_entry.grid(row=1, column=3, padx=5, pady=5)

ctk.CTkButton(frame_edit_phone, text="✏️ Update", command=edit_phone,
              fg_color="#1a5276", hover_color="#154360").grid(row=1, column=4, padx=5)

# --- Search Phone ---
frame_search = ctk.CTkFrame(tab_phones)
frame_search.pack(pady=5, padx=10, fill="x")

search_entry = ctk.CTkEntry(frame_search, placeholder_text="Search by brand or model...", width=300)
search_entry.grid(row=0, column=0, padx=10, pady=8)
ctk.CTkButton(frame_search, text="🔍 Search", command=search_phone).grid(row=0, column=1, padx=5)
ctk.CTkButton(frame_search, text="📋 Show All", command=show_phones).grid(row=0, column=2, padx=5)

# --- Update Stock ---
frame_update = ctk.CTkFrame(tab_phones)
frame_update.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_update, text="Update Stock:").grid(row=0, column=0, padx=(10,5), pady=8)

update_id_entry = ctk.CTkEntry(frame_update, placeholder_text="Phone ID", width=120)
update_id_entry.grid(row=0, column=1, padx=5)

update_stock_entry = ctk.CTkEntry(frame_update, placeholder_text="New Stock", width=120)
update_stock_entry.grid(row=0, column=2, padx=5)

ctk.CTkButton(frame_update, text="🔄 Update Stock", command=update_stock).grid(row=0, column=3, padx=5)

# --- Delete Phone ---
frame_delete = ctk.CTkFrame(tab_phones)
frame_delete.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_delete, text="Delete Phone:").grid(row=0, column=0, padx=(10,5), pady=8)

delete_entry = ctk.CTkEntry(frame_delete, placeholder_text="Phone ID", width=120)
delete_entry.grid(row=0, column=1, padx=5)

ctk.CTkButton(frame_delete, text="🗑️ Delete", command=delete_phone,
              fg_color="#c0392b", hover_color="#922b21").grid(row=0, column=2, padx=5)

# --- Phone Display ---
phone_textbox = ctk.CTkTextbox(tab_phones, width=880, height=220)
phone_textbox.pack(pady=8, padx=10)

# ====================================
# CUSTOMERS TAB
# ====================================

# --- Add Customer ---
frame_cust_add = ctk.CTkFrame(tab_customers)
frame_cust_add.pack(pady=8, padx=10, fill="x")
ctk.CTkLabel(frame_cust_add, text="Add Customer", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=4, pady=(8,4))

cust_name_entry = ctk.CTkEntry(frame_cust_add, placeholder_text="Full Name", width=180)
cust_name_entry.grid(row=1, column=0, padx=5, pady=5)

cust_phone_entry = ctk.CTkEntry(frame_cust_add, placeholder_text="Phone Number", width=160)
cust_phone_entry.grid(row=1, column=1, padx=5, pady=5)

cust_city_entry = ctk.CTkEntry(frame_cust_add, placeholder_text="City", width=140)
cust_city_entry.grid(row=1, column=2, padx=5, pady=5)

ctk.CTkButton(frame_cust_add, text="➕ Add", command=add_customer).grid(row=1, column=3, padx=5)

# --- Edit Customer ---
frame_edit_cust = ctk.CTkFrame(tab_customers)
frame_edit_cust.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_edit_cust, text="Edit Customer", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=5, pady=(8,4))

edit_cust_id_entry = ctk.CTkEntry(frame_edit_cust, placeholder_text="Customer ID", width=120)
edit_cust_id_entry.grid(row=1, column=0, padx=5, pady=5)

edit_cust_name_entry = ctk.CTkEntry(frame_edit_cust, placeholder_text="New Name", width=160)
edit_cust_name_entry.grid(row=1, column=1, padx=5, pady=5)

edit_cust_phone_entry = ctk.CTkEntry(frame_edit_cust, placeholder_text="New Phone", width=140)
edit_cust_phone_entry.grid(row=1, column=2, padx=5, pady=5)

edit_cust_city_entry = ctk.CTkEntry(frame_edit_cust, placeholder_text="New City", width=130)
edit_cust_city_entry.grid(row=1, column=3, padx=5, pady=5)

ctk.CTkButton(frame_edit_cust, text="✏️ Update", command=edit_customer,
              fg_color="#1a5276", hover_color="#154360").grid(row=1, column=4, padx=5)

# --- Search Customer ---
frame_cust_search = ctk.CTkFrame(tab_customers)
frame_cust_search.pack(pady=5, padx=10, fill="x")

cust_search_entry = ctk.CTkEntry(frame_cust_search, placeholder_text="Search by name, phone, or city...", width=300)
cust_search_entry.grid(row=0, column=0, padx=10, pady=8)
ctk.CTkButton(frame_cust_search, text="🔍 Search", command=search_customer).grid(row=0, column=1, padx=5)
ctk.CTkButton(frame_cust_search, text="📋 Show All", command=show_customers).grid(row=0, column=2, padx=5)

# --- Delete Customer ---
frame_cust_delete = ctk.CTkFrame(tab_customers)
frame_cust_delete.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_cust_delete, text="Delete Customer:").grid(row=0, column=0, padx=(10,5), pady=8)

cust_delete_entry = ctk.CTkEntry(frame_cust_delete, placeholder_text="Customer ID", width=130)
cust_delete_entry.grid(row=0, column=1, padx=5)

ctk.CTkButton(frame_cust_delete, text="🗑️ Delete", command=delete_customer,
              fg_color="#c0392b", hover_color="#922b21").grid(row=0, column=2, padx=5)

# --- Customer Display ---
cust_textbox = ctk.CTkTextbox(tab_customers, width=880, height=280)
cust_textbox.pack(pady=8, padx=10)

# ====================================
# ORDERS TAB
# ====================================

# --- Place Order ---
frame_order = ctk.CTkFrame(tab_orders)
frame_order.pack(pady=8, padx=10, fill="x")
ctk.CTkLabel(frame_order, text="Place Order", font=("Arial", 13, "bold")).grid(row=0, column=0, columnspan=4, pady=(8,4))

order_cust_id_entry = ctk.CTkEntry(frame_order, placeholder_text="Customer ID", width=140)
order_cust_id_entry.grid(row=1, column=0, padx=5, pady=5)

order_phone_id_entry = ctk.CTkEntry(frame_order, placeholder_text="Phone ID", width=140)
order_phone_id_entry.grid(row=1, column=1, padx=5, pady=5)

order_qty_entry = ctk.CTkEntry(frame_order, placeholder_text="Quantity", width=120)
order_qty_entry.grid(row=1, column=2, padx=5, pady=5)

ctk.CTkButton(frame_order, text="✅ Place Order", command=place_order,
              fg_color="#1a7a4a", hover_color="#145c38").grid(row=1, column=3, padx=5)

# --- Search Order ---
frame_order_search = ctk.CTkFrame(tab_orders)
frame_order_search.pack(pady=5, padx=10, fill="x")

order_search_entry = ctk.CTkEntry(frame_order_search,
    placeholder_text="Search by Order ID, customer name, phone brand/model, date...", width=380)
order_search_entry.grid(row=0, column=0, padx=10, pady=8)
ctk.CTkButton(frame_order_search, text="🔍 Search", command=search_order).grid(row=0, column=1, padx=5)
ctk.CTkButton(frame_order_search, text="📋 Show All", command=show_orders).grid(row=0, column=2, padx=5)

# --- Delete Order ---
frame_del_order = ctk.CTkFrame(tab_orders)
frame_del_order.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_del_order, text="Delete Order:").grid(row=0, column=0, padx=(10,5), pady=8)

del_order_id_entry = ctk.CTkEntry(frame_del_order, placeholder_text="Order ID", width=130)
del_order_id_entry.grid(row=0, column=1, padx=5)

ctk.CTkButton(frame_del_order, text="🗑️ Delete", command=delete_order,
              fg_color="#c0392b", hover_color="#922b21").grid(row=0, column=2, padx=5)

# --- Edit Order ---
frame_edit_order = ctk.CTkFrame(tab_orders)
frame_edit_order.pack(pady=5, padx=10, fill="x")
ctk.CTkLabel(frame_edit_order, text="Edit Order:").grid(row=0, column=0, padx=(10,5), pady=8)

edit_order_id_entry = ctk.CTkEntry(frame_edit_order, placeholder_text="Order ID", width=130)
edit_order_id_entry.grid(row=0, column=1, padx=5)

edit_order_qty_entry = ctk.CTkEntry(frame_edit_order, placeholder_text="New Quantity", width=130)
edit_order_qty_entry.grid(row=0, column=2, padx=5)

ctk.CTkButton(frame_edit_order, text="✏️ Edit", command=edit_order,
              fg_color="#1a5276", hover_color="#154360").grid(row=0, column=3, padx=5)

# --- Orders Display ---
order_textbox = ctk.CTkTextbox(tab_orders, width=880, height=300)
order_textbox.pack(pady=8, padx=10)

# ====================================
# INIT
# ====================================

def on_closing():
    conn.close()
    app.destroy()

app.protocol("WM_DELETE_WINDOW", on_closing)

show_phones()
show_customers()
show_orders()
refresh_dashboard()

app.mainloop()
