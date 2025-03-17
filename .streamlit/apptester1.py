import streamlit as st
import boto3
import tempfile

# Function to create an S3 client using credentials from Streamlit secrets
def get_s3_client():
    s3 = boto3.client(
        's3',
        aws_access_key_id=st.secrets["AWS_ACCESS_KEY_ID"],
        aws_secret_access_key=st.secrets["AWS_SECRET_ACCESS_KEY"],
        region_name=st.secrets["AWS_DEFAULT_REGION"]
    )
    return s3

# Function to list buckets
def list_buckets():
    s3 = get_s3_client()
    response = s3.list_buckets()
    bucket_names = [bucket['Name'] for bucket in response.get('Buckets', [])]
    return bucket_names

st.title("AWS S3 Integration Test")

# Display list of buckets
if st.button("List S3 Buckets"):
    buckets = list_buckets()
    st.write("Buckets in your account:")
    st.write(buckets)
