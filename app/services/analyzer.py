
def generate_sales_summary(df):

    summary = (
        df.groupby("product")["sales"]
        .sum()
        .to_dict()
    )

    return summary