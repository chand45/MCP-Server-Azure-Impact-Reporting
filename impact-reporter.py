import httpx
from mcp.server.fastmcp import FastMCP
from typing import Any
from azure.identity import DefaultAzureCredential, get_bearer_token_provider
import json
import uuid
import datetime

mcp = FastMCP("impact-reporter")

IMPACT_REPORTER_BASE_URL = "https://management.azure.com"

async def call_impactrp(subscriptionid: str, resourcegroup: str, resourceprovider: str, resourcetype: str, resourcename: str, impactcategory: str) -> str:
    """Reports the impact to Azure. Typically called when customers facing issue with azure infrastructure and they want to let azure know about it."""

    workload_impact_name = str(uuid.uuid4())

    # Construct the URL for the impact report
    url = f"{IMPACT_REPORTER_BASE_URL}/subscriptions/{subscriptionid}/providers/Microsoft.Impact/workloadImpacts/{workload_impact_name}?api-version=2023-12-01-preview"
    impacted_resource_id = f"/subscriptions/{subscriptionid}/resourceGroups/{resourcegroup}/providers/{resourceprovider}/{resourcetype}/{resourcename}"
    # Create a JSON payload for the impact report
    payload = {
        "properties": {
            "impactCategory": f"{impactcategory}",
            "impactedResourceId": f"/subscriptions/{subscriptionid}/resourceGroups/{resourcegroup}/providers/{resourceprovider}/{resourcetype}/{resourcename}",
            "startDateTime": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
    }

    # Get the bearer token
    credential = DefaultAzureCredential()
    accessToken = credential.get_token("https://management.azure.com/.default")
    token = accessToken.token

    # Set up headers with the bearer token
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    async with httpx.AsyncClient(verify=False) as client:
        try:
            response = await client.put(url, headers=headers, json=payload, timeout=30.0)
            return json.dumps(response.json(), indent=2)
        except Exception as e:
            return f"Error reporting impact: {e}"

@mcp.tool()
async def report_impact_to_azure(subscriptionid: str, resourcegroup: str, resourceprovider: str, resourcetype: str, resourcename: str, impactcategory: str) -> str:
    """Reports the impact to Azure. Typically called when customers facing issue with azure infrastructure and they want to let azure know about it.

    Args:
        subscriptionid (str): The Azure subscription ID where the resource is present. Eg: 68fa15fd-eef2-4ca3-a053-bcf268bd7371
        resourcegroup (str): The Azure resource group name where the resource is present. Eg: test-rg
        resourceprovider (str): The Azure resource provider name for the resource. Eg: Microsoft.Compute
        resourcetype (str): The Azure resource type. Eg: virtualMachines
        resourcename (str): The Azure resource name. Eg: test-vm
        impactcategory (str): The impact category denoting the underlying issue. Can be one of: Resource.Connectivity, Resource.Performance, Resource.Availability or Resource.Unknown if the issue is not known.
    """
    # Call the function to report impact to Azure
    response = await call_impactrp(subscriptionid, resourcegroup, resourceprovider, resourcetype, resourcename, impactcategory)
    return response

if __name__ == "__main__":
    # Run the function to report impact to Azure
    mcp.run(transport="stdio")