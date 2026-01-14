# Agentic Finance Analytics Platform

### **The Infrastructure & Pipeline**

I built this project to automate the tedious parts of data analysis. Instead of manually cleaning spreadsheets, I set up a serverless pipeline on AWS. Whenever I upload a raw CSV, a Lambda function triggers immediately, cleans the data, and converts it into Parquet format so it's ready for querying. I used Terraform for all the infrastructure because I wanted the deployment to be consistent and repeatable, so no clicking around in the AWS console. The state is stored remotely in S3, and I set up GitHub Actions to handle the deployments automatically, so the code helps manage itself.

Here is how you can load the infrastructure on your own machine:

```bash
# 1. Clone the repo and setup the Python environment
git clone [https://github.com/aryann4/finance-analytics-project.git](https://github.com/aryann4/finance-analytics-project.git)
python -m venv .venv
source .venv/bin/activate

# 2. Deploy the AWS resources (The "Shared Brain")
cd terraform
terraform init      # Downloads providers and connects to S3
terraform apply     # Builds the S3 buckets, Lambda, and Athena
```

You can ask the agent a question in plain English, and the script figures out the correct SQL query, runs it against the live data in AWS Athena, and explains the result to you. It turns a static database into something you can actually have a conversation with.

Once the infrastructure is ready, here is how you feed it data and start the agent:

```bash
# 1. Upload a CSV (This triggers the Lambda pipeline automatically)
aws s3 cp data/transactions.csv s3://finance-raw-YOUR-BUCKET-ID/

# 2. Add your OpenAI API Key (Create a .env file first)
# OPENAI_API_KEY=sk-proj-...

# 3. Chat with your data
python src/agent.py
```