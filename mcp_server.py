from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.prompts import base
from typer import prompt

mcp = FastMCP("DocumentMCP", log_level="ERROR")


docs = {
    "deposition.md": "This deposition covers the testimony of Angela Smith, P.E.",
    "report.pdf": "The report details the state of a 20m condenser tower.",
    "financials.docx": "These financials outline the project's budget and expenditures.",
    "outlook.pdf": "This document presents the projected future performance of the system.",
    "plan.md": "The plan outlines the steps for the project's implementation.",
    "spec.txt": "These specifications define the technical requirements for the equipment.",
}

#==============================TOOLS===========================================================
# Tool to read a doc
@mcp.tool(
    name="read_doc_contents",
    description="Read the contents of a document and return it as a string.",
)
def read_document(doc_id: str = Field(description="Id of the document to read.")):
    if doc_id not in docs:
        raise ValueError(f"Document with id '{doc_id}' not found.")
    return docs[doc_id]


# Tool to edit a doc
@mcp.tool(
    name="edit_document",
    description="Edit a document by replacing a string in the documents content with a new string.",
)
def edit_document(
    doc_id: str = Field(description="Id of the document that will be edited"),
    old_str: str = Field(
        description="The text to replace. Must match exactly, including whitespace."
    ),
    new_str: str = Field(
        description="The new text to insert in place of the old text."
    ),
):
    if doc_id not in docs:
        raise ValueError(f"Doc with id {doc_id} not found")

    docs[doc_id] = docs[doc_id].replace(old_str, new_str)

# TOOL to get the current date    
@mcp.tool(
    name="get_current_date",
    description="Get the current date.",
)
def get_current_date():
    from datetime import datetime
    return datetime.now().strftime("%Y-%m-%d")

# TOOL to get the ISO date   
@mcp.tool(
    name="get_ISO_string",
    description="Get the current date and time in ISO format.",
)
def get_ISO_string():
    from datetime import datetime
    return datetime.now().isoformat()

@mcp.tool(
    name="refund_resources",
    description="Refunds resources to the user.",
)
def refund_resources(amount: int = Field(description="Amount of resources to refund")):
    # Implement the logic to refund resources here
    return f"Refunded {amount} resources to the user."

@mcp.tool(
    name="get_customer",
    description="Retrieves customer information",
)
def get_customer(customer_id: str = Field(description="Id of the customer to retrieve")):
    # Implement the logic to retrieve customer information here
    return f"Retrieved information for customer with id '{customer_id}'."

@mcp.tool(
    name="lookup_order",
    description="Retrieves order details",
)
def lookup_order(order_id: str = Field(description="Id of the order to retrieve")):
    # Implement the logic to retrieve order details here
    return f"Retrieved details for order with id '{order_id}'."



#==============================RESOURCES===========================================================

# # TODO: Write a resource to return all doc id's
@mcp.resource("docs://documents", mime_type="application/json")
def list_docs() -> list[str]:
    return list(docs.keys())


# TODO: Write a resource to return the contents of a particular doc
@mcp.resource("docs://documents/{doc_id}", mime_type="text/plain")
def read_doc(doc_id: str) -> str:
    if doc_id not in docs:
        raise ValueError(f"Document with id '{doc_id}' not found.")
    return docs[doc_id]


#==============================PROMPTS===========================================================
# TODO: Write a prompt to rewrite a doc in markdown format
@mcp.prompt(
    name="format",
    description="Rewrites the contents of the document in Markdown format.",
)
def format_document(
    doc_id: str = Field(description="Id of the document to format"),
) -> list[base.Message]:
    prompt = f"""
Your goal is to reformat a document to be written with markdown syntax.

The id of the document you need to reformat is:
<document_id>
{doc_id}
</document_id>

Add in headers, bullet points, tables, etc as necessary. Feel free to add in structure.
Use the 'edit_document' tool to edit the document. After the document has been reformatted...
"""

    return [base.UserMessage(prompt)]


# TODO: Write a prompt to summarize a doc


if __name__ == "__main__":
    mcp.run(transport="stdio")
