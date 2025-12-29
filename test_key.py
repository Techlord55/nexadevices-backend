# test_key.py
key = input("Paste your service_role key here: ")
print(f"\nKey length: {len(key)}")
print(f"Starts with: {key[:10]}")
print(f"Valid format: {key.startswith('eyJ')}")

# Create connection string
conn_str = f"postgresql://postgres.tdsyqzawjnybozcrqora:{key}@aws-1-eu-north-1.pooler.supabase.com:6543/postgres?sslmode=require"
print(f"\nYour DATABASE_URL:\n{conn_str}")