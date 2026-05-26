PRODUCT_MAPPING = {
    "Coke": "Coca-Cola",
    "可口可乐": "Coca-Cola",
    "coca cola": "Coca-Cola",
    "COCA-COLA": "Coca-Cola"
}

def normalize_products(df):
    
    df["product"] = (
        df["product"]
        .astype(str)
        .str.strip()
        .replace(PRODUCT_MAPPING)
    )

    return df