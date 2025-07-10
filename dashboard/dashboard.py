import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from babel.numbers import format_currency


# Load dataset
df_shop = pd.read_csv('df_shop.csv')
df_order = pd.read_csv('df_order.csv')
df_shop['order_purchase_timestamp'] = pd.to_datetime(df_shop['order_purchase_timestamp'])

cust_per_category = df_order.groupby(by="product_category_name_english").agg({
        "customer_id": "nunique",
        "seller_id": "nunique",
    }).sort_values(by="customer_id", ascending=False)

active_cust = df_order.groupby(by="order_status").agg({
    "customer_id": "count",
}).sort_values(by="customer_id", ascending=False)

customer_shop = df_shop.groupby(by=(["customer_unique_id"]), as_index=False).agg({
        'order_id': 'count',
        'price': 'sum',
        'payment_value': 'mean'
    }).fillna(0)

customer_shop.rename(columns={'order_id': 'total_orders', 'price': 'expenditure', 'payment_value': 'system_cost'}, inplace=True)
customer_shop['average_expenditure'] = customer_shop['expenditure'] / customer_shop['total_orders']
customer_shop['short_customer_id'] = customer_shop['customer_unique_id'].astype(str).str[:6]

customer_shop = customer_shop.sort_values('expenditure', ascending=False).head(10)

active_total_selling = df_shop.groupby(by="product_category_name_english").agg({
    "customer_id": "nunique",
    "price": ["max", "min", "mean", "sum", "std"]
}).reset_index()

payment_customer_count = df_shop.groupby('payment_type').agg({
    "customer_unique_id": "nunique"
}).sort_values(by=("customer_unique_id"), ascending=False)
payment_customer_count.head()
payment_customer_type = df_shop.groupby(['payment_type', 'payment_sequential', 'order_item_id'])['customer_unique_id'].nunique().reset_index()
payment_customer_type[payment_customer_type['payment_sequential']==1.0].groupby('order_item_id')['customer_unique_id'].sum()
# Group by 'order_id' and 'order_item_id', then aggregate 'payment_type' as a list
payment_combinations = df_shop.groupby(['order_id', 'order_item_id'])['payment_type'].agg(lambda x: ', '.join(x)).reset_index()

# 2. Rename columns for clarity
payment_combinations.columns = ['order_id', 'order_item_id', 'payment_methods_combined']

# 3. Filter orders with two or more payment methods using str.contains(',')
multi_payment_combinations = payment_combinations[payment_combinations['payment_methods_combined'].str.contains(',')]

# 4. Show the first few rows of orders with multiple payment methods
print("Orders with 2 or more payment methods combined for the same order_id and order_item_id:")
multi_payment_combinations.head(10)

df_shop['purchase_month'] = df_shop['order_purchase_timestamp'].dt.to_period('M')
buyers_per_month = df_shop.groupby('purchase_month')['customer_unique_id'].nunique()

# Group by purchase month and product category, counting unique customers
buyers_per_month_category = df_shop.groupby(['purchase_month', 'product_category_name_english'])['customer_unique_id'].nunique()
buyers_per_month_category = buyers_per_month_category.unstack().fillna(0)

# Select the top 20 categories based on total unique buyers
buyers_per_month_category = buyers_per_month_category[buyers_per_month_category.sum().nlargest(10).index]

df_shop['purchase_hour'] = df_shop['order_purchase_timestamp'].dt.hour
df_shop['purchase_minute'] = df_shop['order_purchase_timestamp'].dt.minute
df_shop['purchase_second'] = df_shop['order_purchase_timestamp'].dt.second

orders_per_hour = df_shop.groupby('purchase_hour')['order_id'].count()

# Group by customer and aggregate the data
rfm_df = df_shop.groupby(by="customer_unique_id", as_index=False).agg({
    "order_purchase_timestamp": "max",
    "order_id": "nunique",
    "price": "sum"
})

# Rename columns to match RFM terminology
rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

# Calculate Recency (days since last order)
recent_date = df_shop["order_purchase_timestamp"].max()
rfm_df["recency"] = (recent_date - rfm_df["max_order_timestamp"]).dt.days

# Drop the `max_order_timestamp` as it's no longer needed
rfm_df.drop("max_order_timestamp", axis=1, inplace=True)






# Main content
st.title("E-commerce Dashboard")

st.subheader('Total Customers Based on Order Status')
plt.figure(figsize=(10, 6))

colors = ['#7096D1' if status in ['delivered', 'approved', 'invoiced', 'shipped'] else '#D3D3D3' for status in active_cust.index]

sns.barplot(x=active_cust['customer_id'], y=active_cust.index, palette=colors)

plt.title('Customers based on order status', fontsize=16)
plt.xlabel('amount of customers', fontsize=14)
plt.ylabel('order status', fontsize=14)

for index, value in enumerate(active_cust['customer_id']):
    plt.text(value, index, str(value), va='center')

plt.show()
st.pyplot(plt.gcf())

st.subheader('Top Category Based on Number of Customers and Users')
col1, col2 = st.columns(2)

with col1:
    st.write("Number of Unique Cust for 20 Product Category")
    
    # Plotting the number of customers per category
    plt.figure(figsize=(16, 6))
    bars = cust_per_category['customer_id'].head(20)
    bars.plot(kind='bar', color='#7096D1')

    plt.title('Number of Unique Customers for 20 Product Category')
    plt.xlabel('Product Category')
    plt.ylabel('Number of Customers')
    plt.xticks(rotation=90)
    plt.grid(axis='y', linestyle='None', alpha=1)

    plt.show()
    st.pyplot(plt.gcf())

 
with col2:
    st.write("Number of Unique Seller for 20 Product Category")

    # Plotting the number of sellers per category
    plt.figure(figsize=(16, 9))
    cust_per_category.sort_values(by="seller_id", ascending=False)['seller_id'].head(20).plot(kind='bar', color='lightgreen')

    plt.title('Number of Unique Sellers for 20 Product Category')
    plt.xlabel('Product Category')
    plt.ylabel('Number of Sellers')
    plt.xticks(rotation=90, ha='right')
    plt.grid(axis='y', linestyle='None', alpha=1)

    plt.tight_layout()
    plt.show()
    st.pyplot(plt.gcf())


st.subheader('Customers Preference')
col1, col2 = st.columns(2)

with col1:
    # Sort by mean price
    sorted_selling = active_total_selling.sort_values(by=("price", "sum"), ascending=False).head(10)
    colors_ = ["#7096D1", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

    # Plotting
    plt.figure(figsize=(12, 6))
    sns.barplot(
        y="product_category_name_english",
        x=("price", "sum"),
        data=sorted_selling,
        palette=colors_
    )
    plt.title('Top 10 Product Categories by Sum Price', fontsize=16)
    plt.xlabel('Sum Price', fontsize=14)
    plt.ylabel('Product Category', fontsize=14)
    plt.tight_layout()
    plt.show()
    st.pyplot(plt.gcf())

with col2:
    payment_combination_counts = multi_payment_combinations['payment_methods_combined'].value_counts()

    filtered = payment_combination_counts[payment_combination_counts > 20]
    colors = ["#7096D1", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

    plt.figure(figsize=(10, 6))
    filtered.plot(kind='barh', color=colors)
    plt.xlabel('Frequency')
    plt.ylabel('Payment Method Combinations')
    plt.title('Frequency of Different Payment Method Combinations')
    plt.gca().invert_yaxis()
    plt.show()
    st.pyplot(plt.gcf())

st.subheader('Top 10 Customers')

#Bar plot
fig, ax1 = plt.subplots(figsize=(12, 6))

ax1.bar(customer_shop['short_customer_id'],  customer_shop['expenditure'], color='skyblue', alpha=0.6, label='Total Orders')
ax1.set_xlabel('Customer ID (First 6 Characters)')
ax1.set_ylabel('Total Orders', color='black')
ax1.set_ylabel('Total Expenditure (Price)', color='black')
ax1.tick_params(axis='y', labelcolor='skyblue')
ax2 = ax1.twinx()
ax2.plot(customer_shop['short_customer_id'], customer_shop['total_orders'], color='#FF758F', marker='o', label='Total Expenditure')
ax2.set_ylabel('Total Orders', color='black')
ax2.tick_params(axis='y', labelcolor='#FF758F')

plt.title('Top 10 Customers: Total Orders and Total Expenditure Per Order')
plt.xticks(rotation=45, ha='right')
plt.show()
st.pyplot(plt.gcf())


st.subheader('trends and patterns during the specified analysis period')
col1, col2 = st.columns(2)

# Plotting
plt.figure(figsize=(10, 8))
buyers_per_month_category.plot(kind='line', marker='None', ax=plt.gca())
plt.title('Number of Buyers per Month for Top 10 Product Categories')
plt.xlabel('Month')
plt.ylabel('Number of Unique Buyers')
plt.xticks(rotation=45)
plt.grid()
plt.legend(title='Product Categories', bbox_to_anchor=(1.05, 1), loc='upper left')
plt.tight_layout()
plt.show()
st.pyplot(plt.gcf())
with col1:
    plt.figure(figsize=(14, 6))
    sns.lineplot(x=buyers_per_month.index.astype(str),  y=buyers_per_month.values, marker='o', color="#7096D1")
    plt.title('Number of Buyers per Month')
    plt.xlabel('Month')
    plt.ylabel('Number of Unique Buyers')
    plt.xticks(rotation=45)
    plt.grid()
    plt.show()
    st.pyplot(plt.gcf())

with col2:
    plt.figure(figsize=(14, 6))
    sns.lineplot(x=orders_per_hour.index, y=orders_per_hour.values, marker='o', color='lightgreen')
    plt.title('Distribusi Waktu Pembelian Berdasarkan Jam')
    plt.xlabel('Jam dalam Sehari (0-23)')
    plt.ylabel('Jumlah Order')
    plt.xticks(range(0, 24))
    plt.grid()
    plt.show()
    st.pyplot(plt.gcf())


st.subheader('RFM Analysis')

# Shorten the index of rfm_df (first 6 characters of customer_id)
rfm_df['short_customer_id'] = rfm_df['customer_id'].astype(str).str[:6]

# Plotting
fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(30, 6))

colors = ["#72BCD4", "#D3D3D3", "#D3D3D3", "#D3D3D3", "#D3D3D3"]

# Recency Plot
sns.barplot(y="recency", x="short_customer_id", data=rfm_df.sort_values(by="recency", ascending=False).head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("By Recency (days)", loc="center", fontsize=18)
ax[0].tick_params(axis='x', labelsize=15)

# Frequency Plot
sns.barplot(y="frequency", x="short_customer_id", data=rfm_df.sort_values(by="frequency", ascending=False).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].set_title("By Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelsize=15)

# Monetary Plot
sns.barplot(y="monetary", x="short_customer_id", data=rfm_df.sort_values(by="monetary", ascending=False).head(5), palette=colors, ax=ax[2])
ax[2].set_ylabel(None)
ax[2].set_xlabel(None)
ax[2].set_title("By Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelsize=15)

# Set the title for the whole plot
plt.suptitle("Best Customers Based on RFM Parameters (short_customer_id)", fontsize=20)
plt.show()
st.pyplot(plt.gcf())
