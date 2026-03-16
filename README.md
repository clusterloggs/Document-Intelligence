# Document Intelligence Implementation Guide

**Two Approaches to Building a Document Processing Pipeline with Azure AI Document Intelligence and Microsoft Fabric**

![Azure Document Intelligence](https://img.shields.io/badge/Azure-Document%20Intelligence-0078d4?style=flat-square)
![Python](https://img.shields.io/badge/Python-3.10+-3776ab?style=flat-square)
![Azure Functions](https://img.shields.io/badge/Azure-Functions-0078d4?style=flat-square)
![Microsoft Fabric](https://img.shields.io/badge/Microsoft-Fabric-0078d4?style=flat-square)

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
  - [Approach 1: Azure Function Implementation](#approach-1-azure-function-implementation)
  - [Approach 2: Key Vault Implementation](#approach-2-key-vault-implementation)
- [Architecture Diagrams](#architecture-diagrams)
- [Prerequisites](#prerequisites)
- [Setup Instructions](#setup-instructions)
  - [Common Setup](#common-setup)
  - [Azure Function Implementation Setup](#azure-function-implementation-setup)
  - [Key Vault Implementation Setup](#key-vault-implementation-setup)
- [Deployment](#deployment)
- [Usage Examples](#usage-examples)
- [Security Considerations](#security-considerations)
- [Best Practices](#best-practices)
- [Comparison: When to Use Each Approach](#comparison-when-to-use-each-approach)
- [Troubleshooting](#troubleshooting)

---

## Project Overview

This repository demonstrates **two production-ready approaches** for building document processing pipelines using **Azure AI Document Intelligence** with **Microsoft Fabric notebooks**. Both approaches follow Azure security best practices and are designed for scalable, enterprise-grade deployments.

### What is Azure Document Intelligence?

[Azure Document Intelligence](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/overview?view=doc-intel-4.0.0) (formerly Form Recognizer) is an Azure AI service that uses machine learning to extract structured data from documents, including text, tables, key-value pairs, and handwriting recognition.

### Key Features

✅ Secure credential management  
✅ Scalable document processing  
✅ Support for multiple document models (prebuilt-document, prebuilt-read, etc.)  
✅ Production-ready error handling  
✅ Flexible architecture for different deployment scenarios  

---

## Architecture

### Approach 1: Azure Function Implementation

**Best for:** Centralized processing, isolation of authentication logic, enterprise-scale deployments

**Architecture Flow:**
```
┌─────────────────────────┐
│   Microsoft Fabric      │
│      Notebook           │
└────────────┬────────────┘
             │
             │ HTTP POST (Document)
             │
   ┌─────────▼──────────┐
   │  Azure Function    │
   │  (Middleware)      │
   │                    │
   │  - Auth Logic      │
   │  - API Handling    │
   │  - Error Handling  │
   └────────┬───────────┘
            │
            │ API Call
            │
   ┌────────▼──────────────────┐
   │ Azure Document            │
   │ Intelligence Service      │
   └───────────────────────────┘
```

**How It Works:**

1. The Fabric notebook sends a document to an **Azure Functions HTTP endpoint**
2. The Azure Function receives the document via HTTP POST
3. The function uses **Managed Identity (UAMI)** to authenticate with Azure Document Intelligence (in Azure) or **DefaultAzureCredential** (locally)
4. The function calls the Document Intelligence API to analyze the document
5. Results are returned to the notebook as JSON

**Advantages:**
- Secrets are never exposed in the notebook
- Centralized authentication and error handling
- Easier to audit and monitor document processing
- Can be shared across multiple Fabric workspaces
- Better for compliance and regulated environments

---

### Approach 2: Key Vault Implementation

**Best for:** Direct notebook integration, simplified single-tenant deployments, rapid prototyping

**Architecture Flow:**
```
┌──────────────────────────┐
│  Microsoft Fabric        │
│  Notebook                │
│                          │
│  1. Retrieve Secret      │
└────────────┬─────────────┘
             │
             │ mssparkutils.credentials.getSecret()
             │
   ┌─────────▼──────────┐
   │  Azure Key Vault   │
   │                    │
   │  - API Keys        │
   │  - Credentials     │
   └─────────┬──────────┘
             │
             │ Secret Returned
             │
   ┌─────────▼──────────────────┐
   │ Azure Document              │
   │ Intelligence Service        │
   │ (Direct Call with Key)      │
   └────────────────────────────┘
```

**How It Works:**

1. The Fabric notebook retrieves credentials from **Azure Key Vault** using `mssparkutils.credentials.getSecret()`
2. These credentials are set as environment variables
3. The notebook uses **DefaultAzureCredential** to authenticate with Azure Document Intelligence
4. The notebook calls the API directly and processes documents
5. Results are transformed and stored in a Spark table

**Advantages:**
- Simpler architecture for smaller-scale deployments
- Direct control over processing logic in the notebook
- Reduced network latency
- Easier to develop and test iteratively

---

## Architecture Diagrams

### Data Flow: Azure Function Approach

```
Document Source
      │
      ▼
   Notebook (reads file)
      │
      │ POST /api/dociq_trigger
      │ Body: Binary document data
      │ Params: ?modelId=prebuilt-document
      │
      ▼
   Azure Function HTTP Trigger
      │
      ├─ Authenticate (Managed Identity / DefaultAzureCredential)
      │
      ├─ Create DocumentAnalysisClient
      │
      ├─ Call Document Intelligence API
      │  └─ model: prebuilt-document
      │  └─ document: binary data
      │
      ▼
   Return JSON Response
      {
        "modelId": "prebuilt-document",
        "pages": 5,
        "contentLength": 2048
      }
      │
      ▼
   Notebook (processes response)
      │
      ▼
   Store/Transform Results
```

### Data Flow: Key Vault Approach

```
Document Folder
      │
      ▼
   Notebook starts
      │
      ├─ Retrieve secrets from Key Vault
      │  ├─ ClientID
      │  ├─ TenantID
      │  └─ ClientSecret
      │
      ├─ Initialize DocumentAnalysisClient
      │
      ▼
   Iterate through documents
      │
      ├─ For each file (.pdf, .jpg, .png):
      │
      ├─ Call Document Intelligence API
      │  └─ model: prebuilt-read
      │
      ├─ Extract text and lines
      │
      └─ Append to records list
      │
      ▼
   Create Spark DataFrame
      │
      ▼
   Write to Fabric Table
      └─ alexandria_ocr_output
```

---

## Prerequisites

### Common Requirements

- **Azure Subscription** with active billing
- **Azure AI resources:**
  - Azure Document Intelligence service instance
  - Key Vault (at minimum for Key Vault approach)
- **Microsoft Fabric Workspace** with access to notebooks
- **Python 3.9+** (for local development)
- **Azure CLI** or Azure Portal access for resource management

### Tools and SDKs

```bash
# Python packages (see requirements.txt)
azure-functions           # For Azure Function implementation
azure-identity            # For authentication
azure-ai-formrecognizer   # Document Intelligence SDK
python-dotenv             # For local development
```

### Azure Resources Required

| Resource | Purpose | Approach 1 | Approach 2 |
|----------|---------|-----------|-----------|
| Document Intelligence | Document processing API | ✅ | ✅ |
| Key Vault | Secrets management | ✅ (optional) | ✅ (required) |
| Azure Function App | Middleware/broker | ✅ (required) | ❌ |
| Storage Account | Function code storage | ✅ (required) | ❌ |
| Managed Identity | Secure authentication | ✅ (recommended) | ✅ (optional) |

---

## Setup Instructions

### Common Setup

#### Step 1: Create Azure Resources

Use the Azure Portal or Azure CLI to create the following resources:

**Create Resource Group:**
```bash
az group create \
  --name rg-document-intelligence \
  --location eastus
```

**Create Document Intelligence Service:**
```bash
az cognitiveservices account create \
  --resource-group rg-document-intelligence \
  --name doc-intel-service \
  --kind FormRecognizer \
  --sku S0 \
  --location eastus \
  --yes
```

**Retrieve Document Intelligence Endpoint and Key:**
```bash
az cognitiveservices account show \
  --resource-group rg-document-intelligence \
  --name doc-intel-service \
  --query properties.endpoint \
  --output tsv

az cognitiveservices account keys list \
  --resource-group rg-document-intelligence \
  --name doc-intel-service
```

**Create Key Vault:**
```bash
az keyvault create \
  --resource-group rg-document-intelligence \
  --name kv-document-intel \
  --location eastus
```

#### Step 2: Store Secrets in Key Vault

```bash
# Store Document Intelligence Key
az keyvault secret set \
  --vault-name kv-document-intel \
  --name DocIntelKey \
  --value <YOUR_DOCUMENT_INTELLIGENCE_KEY>

# Store Document Intelligence Endpoint
az keyvault secret set \
  --vault-name kv-document-intel \
  --name DocIntelEndpoint \
  --value <YOUR_DOCUMENT_INTELLIGENCE_ENDPOINT>

# For Key Vault approach, also store credentials
az keyvault secret set \
  --vault-name kv-document-intel \
  --name ClientID \
  --value <YOUR_CLIENT_ID>

az keyvault secret set \
  --vault-name kv-document-intel \
  --name TenantID \
  --value <YOUR_TENANT_ID>

az keyvault secret set \
  --vault-name kv-document-intel \
  --name ClientSecret \
  --value <YOUR_CLIENT_SECRET>
```

---

### Azure Function Implementation Setup

**Location:** `AzureFunction_Implementation/`

#### Step 1: Create Function App

```bash
# Create Storage Account (required for Function App)
az storage account create \
  --resource-group rg-document-intelligence \
  --name stgdocumentintel \
  --location eastus \
  --sku Standard_LRS

# Create Function App (Python, Linux)
az functionapp create \
  --resource-group rg-document-intelligence \
  --consumption-plan-location eastus \
  --runtime python \
  --functions-version 4 \
  --name func-document-intelligence \
  --storage-account stgdocumentintel
```

#### Step 2: Create Managed Identity (Recommended for Azure)

```bash
# Create User-Assigned Managed Identity
az identity create \
  --resource-group rg-document-intelligence \
  --name uami-doc-intel

# Get Identity Client ID
az identity show \
  --resource-group rg-document-intelligence \
  --name uami-doc-intel \
  --query clientId \
  --output tsv
```

#### Step 3: Assign RBAC Roles

Grant the Managed Identity access to Document Intelligence and Key Vault:

```bash
# Get identity principal ID
PRINCIPAL_ID=$(az identity show \
  --resource-group rg-document-intelligence \
  --name uami-doc-intel \
  --query principalId \
  --output tsv)

# Get Document Intelligence resource ID
DOC_INTEL_ID=$(az cognitiveservices account show \
  --resource-group rg-document-intelligence \
  --name doc-intel-service \
  --query id \
  --output tsv)

# Assign "Cognitive Services User" role
az role assignment create \
  --assignee-object-id $PRINCIPAL_ID \
  --role "Cognitive Services User" \
  --scope $DOC_INTEL_ID

# Grant Key Vault access (if using Key Vault for configuration)
az keyvault set-policy \
  --name kv-document-intel \
  --object-id $PRINCIPAL_ID \
  --secret-permissions get list
```

#### Step 4: Assign Managed Identity to Function App

```bash
# Assign managed identity to Function App
az functionapp identity assign \
  --resource-group rg-document-intelligence \
  --name func-document-intelligence \
  --identities /subscriptions/{subscriptionId}/resourcegroups/rg-document-intelligence/providers/Microsoft.ManagedIdentity/userAssignedIdentities/uami-doc-intel

# Add the identity as a default principal
az resource update \
  --ids /subscriptions/{subscriptionId}/resourceGroups/rg-document-intelligence/providers/Microsoft.Web/sites/func-document-intelligence/config/identity \
  --set properties.userAssignedIdentities./subscriptions/{subscriptionId}/resourcegroups/rg-document-intelligence/providers/Microsoft.ManagedIdentity/userAssignedIdentities/uami-doc-intel={}
```

#### Step 5: Configure App Settings

```bash
# Get Document Intelligence endpoint
ENDPOINT=$(az cognitiveservices account show \
  --resource-group rg-document-intelligence \
  --name doc-intel-service \
  --query properties.endpoint \
  --output tsv)

# Get Managed Identity Client ID
UAMI_CLIENT_ID=$(az identity show \
  --resource-group rg-document-intelligence \
  --name uami-doc-intel \
  --query clientId \
  --output tsv)

# Configure Function App settings
az functionapp config appsettings set \
  --name func-document-intelligence \
  --resource-group rg-document-intelligence \
  --settings \
  DOCINTEL_ENDPOINT=$ENDPOINT \
  UAMI_CLIENT_ID=$UAMI_CLIENT_ID
```

#### Step 6: Deploy Function Code

```bash
# Navigate to function directory
cd AzureFunction_Implementation

# Install Python dependencies locally
pip install -r requirements.txt

# Deploy using Azure Functions Core Tools
# (install from: https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local)
func azure functionapp publish func-document-intelligence --build remote
```

> **Note:** Ensure you have [Azure Functions Core Tools](https://docs.microsoft.com/en-us/azure/azure-functions/functions-run-local) installed locally.

#### Step 7: Verify Deployment

```bash
# Get function URL
az functionapp show-details \
  --resource-group rg-document-intelligence \
  --name func-document-intelligence \
  --query defaultHostName \
  --output tsv
```

Function URL will be: `https://{functionAppName}.azurewebsites.net/api/dociq_trigger`

---

### Key Vault Implementation Setup

**Location:** `Key_Vault_Implementation/`

#### Step 1: Grant Fabric Workspace Access to Key Vault

1. **Open Azure Portal** → Key Vault → `kv-document-intel`
2. **Go to:** Access control (IAM) → Add role assignment
3. **Select role:** `Key Vault Secrets User`
4. **Assign to:** Your Fabric workspace's Managed Identity
   - Navigate to Fabric workspace settings to find the workspace principal

Alternatively, using CLI:

```bash
# Get Fabric workspace principal ID (obtained from workspace settings)
WORKSPACE_PRINCIPAL_ID="<your-fabric-workspace-principal-id>"

# Get Key Vault resource ID
KV_ID=$(az keyvault show \
  --name kv-document-intel \
  --query id \
  --output tsv)

# Create policy for Key Vault secrets access
az keyvault set-policy \
  --name kv-document-intel \
  --object-id $WORKSPACE_PRINCIPAL_ID \
  --secret-permissions get list
```

#### Step 2: Verify Document Intelligence Configuration

Ensure these secrets are in Key Vault:
- `ClientID` - Azure AD Application ID
- `TenantID` - Azure AD Tenant ID
- `ClientSecret` - Azure AD Application Secret
- `DocIntelEndpoint` - Document Intelligence service endpoint

#### Step 3: Prepare Fabric Notebook

1. **Open or create** a new Fabric notebook
2. **Copy the code** from `Key_Vault_Implementation/DocIQ.py`
3. **Update these placeholders:**

```python
vault_url = "https://kv-document-intel.vault.azure.net/"  # Update with your vault URL

endpoint = "https://your-doc-intel.cognitiveservices.azure.com/"  # Update with your endpoint

folder_path = Path("/lakehouse/{workspace-id}/input/raw/")  # Update with your Lakehouse path
```

4. **Save and run** the notebook

---

## Deployment

### Approach 1: Azure Function - CI/CD Pipeline (Optional)

To automate deployments, set up a GitHub Actions or Azure DevOps pipeline:

**GitHub Actions Example (.github/workflows/deploy.yml):**

```yaml
name: Deploy Azure Function

on:
  push:
    branches: [ main ]
    paths: [ 'AzureFunction_Implementation/**' ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Install Azure Functions Core Tools
      run: |
        curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor > microsoft.gpg
        sudo mv microsoft.gpg /etc/apt/trusted.gpg.d/
        sudo sh -c 'echo "deb [arch=amd64,arm64,armhf signed-by=/etc/apt/trusted.gpg.d/microsoft.gpg] https://packages.microsoft.com/repos/azure-cli/ jammy main" > /etc/apt/sources.list.d/azure-cli.list'
        sudo apt-get update
        sudo apt-get install azure-functions-core-tools-4
    
    - name: Install dependencies
      run: |
        pip install -r AzureFunction_Implementation/requirements.txt
    
    - name: Deploy Function
      env:
        AZURE_FUNCTIONAPP_PUBLISH_PROFILE: ${{ secrets.AZURE_FUNCTIONAPP_PUBLISH_PROFILE }}
      run: |
        cd AzureFunction_Implementation
        func azure functionapp publish func-document-intelligence --build remote
```

### Approach 2: Key Vault - Notebook Notebook Scheduling

To run the Key Vault notebook on a schedule:

1. **Open Fabric Workspace** → Notebook settings
2. **Enable schedule** → Set frequency (hourly, daily, weekly)
3. **Configure notifications** for job completion or failures

---

## Usage Examples

### Approach 1: Calling Azure Function from Notebook

```python
import requests
import json
from pathlib import Path
from notebookutils import mssparkutils

# Configuration
FUNCTION_URL = "https://func-document-intelligence.azurewebsites.net/api/dociq_trigger"
FUNCTION_KEY = mssparkutils.credentials.getSecret("https://kv-document-intel.vault.azure.net/", "FunctionKey")

# Read document from lakehouse
document_path = Path("/lakehouse/{workspace-id}/input/sample.pdf")
with open(document_path, "rb") as f:
    document_data = f.read()

# Call Azure Function
headers = {
    "x-functions-key": FUNCTION_KEY,
    "Content-Type": "application/octet-stream"
}

params = {
    "modelId": "prebuilt-document"  # Can use: prebuilt-read, prebuilt-invoice, etc.
}

response = requests.post(
    FUNCTION_URL,
    data=document_data,
    headers=headers,
    params=params
)

if response.status_code == 200:
    result = response.json()
    print(f"Document processed successfully")
    print(f"Pages: {result['pages']}")
    print(f"Content length: {result['contentLength']}")
else:
    print(f"Error: {response.status_code} - {response.text}")
```

### Approach 2: Direct Document Intelligence from Notebook

```python
from notebookutils import mssparkutils
import os
from pathlib import Path
from azure.ai.formrecognizer import DocumentAnalysisClient
from azure.core.credentials import AzureKeyCredential
from azure.identity import DefaultAzureCredential
import pandas as pd
from pyspark.sql import SparkSession

# Initialize Spark
spark = SparkSession.builder.getOrCreate()

# Retrieve secrets from Key Vault
vault_url = "https://kv-document-intel.vault.azure.net/"

os.environ["AZURE_CLIENT_ID"] = mssparkutils.credentials.getSecret(vault_url, "ClientID")
os.environ["AZURE_TENANT_ID"] = mssparkutils.credentials.getSecret(vault_url, "TenantID")
os.environ["AZURE_CLIENT_SECRET"] = mssparkutils.credentials.getSecret(vault_url, "ClientSecret")

# Initialize Document Intelligence Client
endpoint = "https://your-doc-intel.cognitiveservices.azure.com/"
credential = DefaultAzureCredential()

client = DocumentAnalysisClient(
    endpoint=endpoint,
    credential=credential
)

# Process documents
folder_path = Path("/lakehouse/{workspace-id}/input/raw/")
records = []
model_id = "prebuilt-read"

for file in folder_path.iterdir():
    if file.suffix.lower() in [".jpg", ".jpeg", ".png", ".pdf"]:
        print(f"Processing: {file.name}")
        
        with open(file, "rb") as f:
            poller = client.begin_analyze_document(
                model_id=model_id,
                document=f
            )
        
        result = poller.result()
        
        # Extract text
        lines = []
        for page in result.pages:
            for line in page.lines:
                lines.append(line.content)
        
        extracted_text = "\n".join(lines)
        
        # Store record
        records.append({
            "file_name": file.name,
            "file_type": file.suffix.lower(),
            "content": extracted_text,
            "extracted_at": datetime.utcnow().isoformat()
        })

# Create Spark table
df = pd.DataFrame(records)
spark_df = spark.createDataFrame(df)
spark_df.write.mode("overwrite").saveAsTable("alexandria_ocr_output")

print(f"Processed {len(records)} documents. Results saved to 'alexandria_ocr_output' table.")
```

---

## Security Considerations

### 1. **Credential Management**

✅ **Do:**
- Store credentials in Azure Key Vault
- Use Managed Identities for service-to-service authentication
- Use `DefaultAzureCredential` for automatic credential discovery
- Rotate secrets regularly (every 90 days recommended)
- Audit Key Vault access logs

❌ **Don't:**
- Hardcode credentials in code or notebooks
- Store secrets in environment variables without encryption
- Share credentials across multiple services
- Commit `.env` files or credentials to source control

### 2. **Network Security**

```bash
# Enable Key Vault firewall (Azure CLI)
az keyvault update \
  --name kv-document-intel \
  --enable-purge-protection true \
  --default-action Deny \
  --bypass AzureServices

# Whitelist specific IP addresses
az keyvault network-rule add \
  --name kv-document-intel \
  --ip-address <YOUR_IP_RANGE>
```

### 3. **Function App Security**

For Azure Function implementations:

```bash
# Restrict to specific IPs (if publicly accessible)
az functionapp config access-restriction add \
  --resource-group rg-document-intelligence \
  --name func-document-intelligence \
  --rule-name AllowOnlyFabric \
  --action Allow \
  --priority 100 \
  --ip-address <FABRIC_IP_RANGE>

# Require HTTPS only
az functionapp config set \
  --resource-group rg-document-intelligence \
  --name func-document-intelligence \
  --http20-enabled true
```

### 4. **Audit and Monitoring**

Enable Azure Monitor and Application Insights:

```python
# Function App logging example
import logging
import azure.functions as func

logging.warning(f"Processing document of size: {len(doc_bytes)} bytes")
```

Monitor logs in Azure Portal:
1. Go to Function App → Application Insights
2. View live metrics and traces
3. Set up alerts for failures

### 5. **RBAC Best Practices**

| Role | Purpose | Scope |
|------|---------|-------|
| `Cognitive Services User` | Document Intelligence API access | Document Intelligence resource |
| `Key Vault Secrets User` | Read secrets from Key Vault | Key Vault resource |
| `Contributor` | Manage Azure resources | Resource group |
| `Function App Contributor` | Deploy and manage functions | Function App |

---

## Best Practices

### 1. **Error Handling and Logging**

```python
# Always use try-except with logging
import logging

try:
    result = client.begin_analyze_document(model_id=model_id, document=doc_bytes).result()
except Exception as e:
    logging.error(f"Document analysis failed: {str(e)}", exc_info=True)
    # Return appropriate error response
```

### 2. **Batch Processing**

```python
# Process documents in batches for better performance
from concurrent.futures import ThreadPoolExecutor, as_completed

def process_document(file_path, client, model_id):
    with open(file_path, "rb") as f:
        poller = client.begin_analyze_document(model_id=model_id, document=f)
    return poller.result()

with ThreadPoolExecutor(max_workers=5) as executor:
    futures = [
        executor.submit(process_document, file, client, "prebuilt-read")
        for file in documents
    ]
    
    for future in as_completed(futures):
        result = future.result()
        # Process result
```

### 3. **Timeout and Retry Configuration**

```python
from azure.core.retry import Retry
from azure.core.pipeline.policies import RetryPolicy

# Configure retry policy
retry_policy = Retry(
    total=3,
    backoff_factor=0.5,
    status_forcelist=[429, 500, 502, 503, 504]
)

# Applied automatically with DefaultAzureCredential
```

### 4. **Document Size Validation**

```python
# Document Intelligence has size limits (max 50 MB)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50 MB

if len(doc_bytes) > MAX_FILE_SIZE:
    raise ValueError(f"Document exceeds maximum size of {MAX_FILE_SIZE} bytes")
```

### 5. **Model Selection**

Choose the appropriate model based on use case:

| Model | Best For | Example |
|-------|----------|---------|
| `prebuilt-read` | OCR, text extraction | Books, articles, scanned documents |
| `prebuilt-document` | Forms, invoices, receipts | Expense reports, receipts |
| `prebuilt-invoice` | Invoice processing | Vendor invoices |
| `prebuilt-identity-document` | ID extraction | Driver's license, passport |

### 6. **Pagination for Large Results**

```python
# Handle large documents with multiple pages
for page_num, page in enumerate(result.pages):
    print(f"Processing page {page_num + 1} of {len(result.pages)}")
    for line in page.lines:
        # Process line
        pass
```

### 7. **Cost Optimization**

- Use **S0 tier** for production; F0 for development/testing
- Monitor API call counts in Azure Portal
- Consider pre-processing documents (compress images, remove unnecessary pages)
- Estimate costs: $1-2 per 1000 pages processed (check pricing page)

---

## Comparison: When to Use Each Approach

### Quick Decision Matrix

| Requirement | Approach 1 (Function) | Approach 2 (Key Vault) |
|-------------|----------------------|------------------------|
| **Isolation of Secrets** | ✅ Excellent | ✅ Good |
| **Centralized Processing** | ✅ Yes | ❌ No |
| **Ease of Setup** | ❌ Complex | ✅ Simple |
| **Multi-workspace Sharing** | ✅ Yes | ❌ Per workspace |
| **Development Speed** | ❌ Slower | ✅ Faster |
| **Scalability** | ✅ High | ⚠️ Medium |
| **Cost** | ⚠️ Additional compute | ✅ Lower |
| **Monitoring** | ✅ Detailed | ⚠️ Notebook-level |
| **Production Ready** | ✅ Yes | ✅ Yes |

### Detailed Comparison

#### **Approach 1: Azure Function Implementation**

**Choose this if:**
- ✅ You need to share document processing logic across multiple Fabric workspaces
- ✅ You require strong separation between authentication and processing logic
- ✅ You need detailed monitoring and audit logs for compliance
- ✅ You have high-volume document processing (1000s per day)
- ✅ You need to integrate with other systems beyond Fabric

**Avoid if:**
- ❌ You have a single small-scale Fabric workspace
- ❌ You need rapid prototyping and quick iterations
- ❌ Your organization has budget constraints

**Cost:** ~$0.20/month (consumption plan F1) + API calls

---

#### **Approach 2: Key Vault Implementation**

**Choose this if:**
- ✅ You have a single Fabric workspace for document processing
- ✅ You need a quick proof-of-concept or MVP
- ✅ You prefer simplicity over complexity
- ✅ All processing logic can be contained in the notebook
- ✅ You have lower document volume (< 1000 documents/day)

**Avoid if:**
- ❌ You need to share functions across multiple workspaces
- ❌ You need enterprise-scale monitoring and auditing
- ❌ You require microservices architecture patterns

**Cost:** Only API calls (no additional compute costs)

---

## Troubleshooting

### Azure Function Implementation Issues

#### Issue 1: "Missing UAMI_CLIENT_ID in Azure app settings"

**Cause:** Managed Identity client ID not configured in Function App settings

**Solution:**
```bash
# Verify Managed Identity assignment
az functionapp identity show \
  --resource-group rg-document-intelligence \
  --name func-document-intelligence

# Re-assign the identity and app settings
az functionapp config appsettings set \
  --name func-document-intelligence \
  --resource-group rg-document-intelligence \
  --settings UAMI_CLIENT_ID=<client-id-from-above>
```

#### Issue 2: "Authentication failed: Invalid credentials"

**Cause:** Managed Identity lacks necessary RBAC role

**Solution:**
```bash
# Verify role assignment
PRINCIPAL_ID=$(az identity show \
  --resource-group rg-document-intelligence \
  --name uami-doc-intel \
  --query principalId \
  --output tsv)

DOC_INTEL_ID=$(az cognitiveservices account show \
  --resource-group rg-document-intelligence \
  --name doc-intel-service \
  --query id \
  --output tsv)

# Verify Cognitive Services User role
az role assignment list \
  --assignee-object-id $PRINCIPAL_ID \
  --scope $DOC_INTEL_ID
```

#### Issue 3: "Function timeout (duration exceeded)"

**Cause:** Large documents taking too long to process

**Solution:**
- Chunk documents into smaller files
- Increase function timeout in `host.json`:
  ```json
  {
    "functionTimeout": "00:10:00"
  }
  ```
- Upgrade to a higher tier Function App plan

---

### Key Vault Implementation Issues

#### Issue 1: "SecretCredentialError: Failed to get the list of secrets"

**Cause:** Fabric workspace lacks Key Vault access permissions

**Solution:**
```bash
# Re-apply Key Vault permissions for Fabric workspace principal
WORKSPACE_PRINCIPAL_ID="<fabric-workspace-id>"

az keyvault set-policy \
  --name kv-document-intel \
  --object-id $WORKSPACE_PRINCIPAL_ID \
  --secret-permissions get list
```

#### Issue 2: "DocumentAnalysisClient initialization failed"

**Cause:** Incorrect endpoint format or authentication failure

**Solution:**
```python
# Verify endpoint format
endpoint = "https://your-doc-intel.cognitiveservices.azure.com/"  # Correct
# NOT: "https://your-doc-intel.cognitiveservices.azure.com"  (missing trailing slash in some cases)

# Verify credentials
credential = DefaultAzureCredential(
    exclude_shared_token_cache_credential=True,
    exclude_web_browser_credential=True
)
```

#### Issue 3: "Lakehouse path not found"

**Cause:** Incorrect Lakehouse path in notebook

**Solution:**
```python
from pathlib import Path

# Navigate to Lakehouse in Fabric
# Copy the path from the file explorer
# Example: /lakehouse/workspace-id/input/raw/

# Verify path exists
folder_path = Path("/lakehouse/{workspace-id}/input/raw/")
if folder_path.exists():
    print(f"Path exists: {list(folder_path.iterdir())}")
else:
    print(f"Path not found: {folder_path}")
```

---

### Common Issues (Both Approaches)

#### Issue: "Document Intelligence quota exceeded"

**Solution:**
```bash
# Check usage in Azure Portal:
# 1. Go to Document Intelligence resource
# 2. Check "Metrics" → "API Calls"
# 3. If at quota limit, upgrade service tier:

az cognitiveservices account update \
  --name doc-intel-service \
  --resource-group rg-document-intelligence \
  --sku S0
```

#### Issue: "Unsupported file format"

**Cause:** Document is in an unsupported format

**Supported formats by Document Intelligence:**
- ✅ PDF
- ✅ PNG, JPG, JPEG, BMP, TIFF
- ❌ DOCX, XLSX, PPTX (not directly supported)

**Solution:** Convert documents to PDF or image format before processing

---

## Additional Resources

### Microsoft Documentation
- [Azure Document Intelligence Documentation](https://learn.microsoft.com/en-us/azure/ai-services/document-intelligence/)
- [Azure Functions Python Developer Guide](https://learn.microsoft.com/en-us/azure/azure-functions/functions-reference-python)
- [Microsoft Fabric Notebooks](https://learn.microsoft.com/en-us/fabric/data-engineering/how-to-use-notebook)
- [Azure Key Vault Documentation](https://learn.microsoft.com/en-us/azure/key-vault/)

### SDK References
- [azure-ai-formrecognizer Python SDK](https://learn.microsoft.com/en-us/python/api/azure-ai-formrecognizer/)
- [azure-identity Python SDK](https://learn.microsoft.com/en-us/python/api/azure-identity/)
- [azure-functions Python SDK](https://learn.microsoft.com/en-us/python/api/azure-functions/)

### Pricing
- [Document Intelligence Pricing](https://azure.microsoft.com/en-us/pricing/details/cognitive-services/form-recognizer/)
- [Azure Functions Pricing](https://azure.microsoft.com/en-us/pricing/details/functions/)
- [Key Vault Pricing](https://azure.microsoft.com/en-us/pricing/details/key-vault/)

---

## Contributing

To contribute to this repository:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/your-feature`
3. **Make your changes** and test thoroughly
4. **Commit with clear messages:** `git commit -m "Add [feature name]"`
5. **Push to your fork:** `git push origin feature/your-feature`
6. **Create a Pull Request** with a detailed description

---

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE) file for details.

---

## Support

For issues or questions:

1. **Check the Troubleshooting section** above
2. **Review Azure Documentation** linked in Resources
3. **Open a GitHub Issue** with:
   - Clear description of the problem
   - Steps to reproduce
   - Error messages and logs
   - Your environment (Python version, Azure SDK versions)

---

## Authors

**Document Intelligence Implementation Guide**
- Built following Microsoft Azure best practices
- Tested with Python 3.10+ and Azure SDK v1.0+
- Compatible with Microsoft Fabric notebooks (2024+)

---

**Last Updated:** March 2026  
**Status:** Production Ready
