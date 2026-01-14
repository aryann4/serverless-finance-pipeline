import os
import time
import boto3
from openai import OpenAI
from dotenv import load_dotenv

# 1. Load your secret key
load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# 2. AWS Config (The "Tool")
# Make sure these match your Athena setup!
DATABASE = 'finance_db'
TABLE = 'transactions'
OUTPUT_LOCATION = 's3://finance-athena-results-20260103031326179500000001/'  # <--- UPDATE THIS if needed (check your S3 buckets)

athena = boto3.client('athena', region_name='us-east-1')


def run_athena_query(query):
    """The 'Hand': Executes a SQL query on AWS and returns the results."""
    print(f"🤖 Agent is running SQL: {query}")

    # Start the query execution
    response = athena.start_query_execution(
        QueryString=query,
        QueryExecutionContext={'Database': DATABASE},
        ResultConfiguration={'OutputLocation': OUTPUT_LOCATION}
    )
    query_execution_id = response['QueryExecutionId']

    # Wait for it to finish
    while True:
        stats = athena.get_query_execution(QueryExecutionId=query_execution_id)
        status = stats['QueryExecution']['Status']['State']
        if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
            break
        time.sleep(1)  # Wait 1 second before checking again

    if status == 'FAILED':
        return f"Error: {stats['QueryExecution']['Status']['StateChangeReason']}"

    # Get the results
    results = athena.get_query_results(QueryExecutionId=query_execution_id)

    # Clean up the weird AWS format into a readable list
    rows = []
    for row in results['ResultSet']['Rows']:
        rows.append([data.get('VarCharValue', 'NULL') for data in row['Data']])

    return rows


def talk_to_agent(user_question):
    """The 'Brain': Translates English -> SQL -> English"""

    # Step 1: Ask GPT to write the SQL
    schema_context = f"""
    You are a Data Analyst Agent. You have access to an AWS Athena table named '{DATABASE}.{TABLE}'.
    The columns are: Date (string), Description (string), Category (string), Amount (float), Type (string).
    'Type' can be 'Credit' (income) or 'Debit' (expense).

    Write a Presto SQL query to answer this question: "{user_question}"
    Return ONLY the raw SQL query. Do not wrap it in markdown or quotes.
    """

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": schema_context}]
    )
    sql_query = response.choices[0].message.content.strip().replace("```sql", "").replace("```", "")

    # Step 2: Run the tool
    data = run_athena_query(sql_query)

    # Step 3: Ask GPT to explain the answer
    analysis_context = f"""
    User Question: "{user_question}"
    SQL Query Run: "{sql_query}"
    Data Returned: {data}

    Explain the answer to the user in a friendly, professional way. 
    If the data is a list of transactions, summarize the key findings.
    """

    final_response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": analysis_context}]
    )

    print("\n💬 AGENT RESPONSE:")
    print(final_response.choices[0].message.content)
    print("-" * 50)


if __name__ == "__main__":
    print("Agent is online! (Type 'quit' to exit)")
    while True:
        q = input("\nAsk a question about your finances: ")
        if q.lower() in ['quit', 'exit']:
            break
        talk_to_agent(q)