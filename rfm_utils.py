import pandas as pd

def calculate_rfm(transactions):

    transactions = transactions.copy()
    transactions['order_date'] = pd.to_datetime(
        transactions['order_date']
    )

    snapshot_date = (
        transactions['order_date'].max()
        + pd.Timedelta(days=30)
    )

    rfm = transactions.groupby('customer_id').agg(
        recency=('order_date', lambda x: (snapshot_date - x.max()).days),
        frequency=('sales_order_id', 'nunique'),
        monetary=('paid_total_EGP', 'sum')
    )

    return rfm[['recency', 'frequency', 'monetary']]