# TenantRights Advisor

TenantRights Advisor is an application that utilises Retrieval Augmented Generation (RAG) to answer tenant queries regarding their rights.

In the application a user can enter a query related to tenancy rights and will be provided an answer to their query along with a link to the external source that was used to answer their query.

The image below shows the user interface for TenantRights Advisor.

![Alt](/assets/base.png "base")

The below images show the results output by TenantRights Advisor in response to several user queries.

![Alt](/assets/curtains.png "curtains")

![Alt](/assets/fish.png "fish")

![Alt](/assets/selling.png "selling")

## RAG

RAG is an architecture that uses an external knowledge base and a Large Language Model (LLM) to generate answers to user queries. It combines an information retrieval component with a text generator model to provide relevant answers to user queries.

* Information Retrieval: In the retrieval phase, algorithms search for and retrieve snippets of information relevant to the user’s prompt or question. The relevant information for retrieval is normally stored in a vector database which stores information as word embeddings. 

* Content generation: Information retrieved is appended to a user’s prompt to create an answer tailored to the user in that instant. The generative text model can return the appropriate response, with the support of the retrieved information as additional context to help with response generation.

The image below provides an overview of the basic RAG architecture.

![Alt](/assets/basic_rag_architecture.png "Basic RAG architecture")

Within the basic RAG architecture:
1. The user provides a query (e.g. "How much notice do I need to provide to end a tenancy?")
2. The query is matched with relevant documents in the vector database
3. The most relevant documents are retrieved
4. A query prompt is created for an LLM which includes the user's original query and the context retrieved from the vector database
5. The LLM provides a response to the user based on the prompt provided

### Advantages of using RAG
RAG's improvment over just using an LLM is grounding the LLM with external knowledge retrieved from the vector database. There are three main benefits to doing this:

* It ensures the model has access to the most current, reliable facts.

* Users have access to the model’s sources, ensuring that its claims can be checked for accuracy and ultimately trusted. This allows users to cross-reference a model’s answers with the original material so they can be confident it is accurate.

* There is not a need to continuously train the model on new data and update its parameters as circumstances evolve. In this way, RAG can lower the computational and financial costs of running LLM-powered chatbots in an enterprise setting.

## Tenancy Rights

The chosen use case for this project was tenancy rights. This means that the RAG application requires a source of information on tenancy rights that can be used as context to pass to an LLM to assist in answering user queries.

Information on tenancy rights was obtained from two publicly available sources:
* [Aratohu Tenant Advocacy](https://tenant.aratohu.nz/) 
* [Citizens Advice Bureau](https://cab.org.nz/) 


Both of these websites include a range of knowledge articles that were used as the basis for the vector database. It is the content of the knowledge articles that is retrieved and then passed to the LLM as context for answering user queries.

## Solution Implemented

The solution implemented uses the base RAG architecture with some enhanced RAG techniques incorporated. The image below shows the solution implemented.

![Alt](/assets/tenancy_rag_architecture.png "Basic RAG architecture")

The end-to-end flow for this solution is:
1. User enters a query prompt with their question relating to tenancy rights.
2. User query is passed to an LLM to refine into a step-back qeury.
3. The step-back query is matched against chunks in the document database.
4. The entire document for the matched chunk is retrieved.
5. A prompt is created which consists of instruction to the LLM, the retrieved document, step-back query and original user query.
6. This prompt is passed to the LLM (in this case Google's Gemini) which returns an answer to the user query. 


### Step-back query
A step-back query is where an LLM is used to create a more generic version of a user query. The idea behind this is that a more generic version of the user query will provide a better match to the documents in the vector database. 


### Expanded context window
The default approach for a vector database is to store chunks of source documents to match against and pass as context to an LLM. A chunk will generally be a single sentence or paragraph within a document. In this application the documents are the knowledge articles and the chunks are sentences/paragraphs from the knowledge articles.

Expanding the context window involves expanding on the chunk so that increased context is passed to the LLM answering the question. In this solution the entire document from the matched chunk is retireved and included in the prompt for generating a response.

## Included in this repository
The table below describes the contents of this repository.

| repository folder | description                                                                                                                                                                                                                                                                                                               |
|-------------------|---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| app_prod          | The TenantRights Advisor application implemented as a dash app that utilises a chroma vector database for information retrieval and calls out to Google Gemini LLM via Langchain for generating a step-back query and generating an answer.                                                                                    |
| app_test          | A test version of the TenantRights Advisor application. This test version uses the same chroma vector database and also utilises Google Gemini LLM. Where it differs is that it provides a user interface to alter the query sent to the LLM so different versions of the query sent to the LLM could be tested.               |
| assets            | Stores PNG files used in the README file.                                                                                                                                                                                                                                                                                 |
| chroma            | Chroma is the vector database used in this application. This stores the chroma database created by the script create_database.py                                                                                                                                                                                          |
| data              | Stores data used in the application. The aratohu and cab folders include the knowledge articles used to create the vector database. The queries folder contains sample queries sourced from the NZ Legal Advice subreddit that were used to test the application. The file source_links.json includes links to the source of knowledge articles. |
| notebooks         | Stores the notebook scrape_CAB.ipynb which includes code used to scrape knowledge articles from CAB.                                                                                                                                                                                                         |
| scripts           | Scripts used in the application. create_database.py includes code to create the chroma database used in the application.                                                                                                                                                                                                 |                                                                                                                                                                                               |


## Prompt Templates
Below are the prompt templates used in the solution.

### Query refinement prompt

You are an advisor on tenancy rights. 
Your task is to step back and paraphrase a question from a tenant to a more generic step-back question so that is easier to answer in reference to tenancy law. 

Here are a few examples:
Original Question: Which position did Knox Cunningham hold from May 1955 to Apr 1956?
Stepback Question: Which positions have Knox Cunning- ham held in his career?

Original Question: Who was the spouse of Anna Karina from 1968 to 1974?
Stepback Question: Who were the spouses of Anna Karina?

Original Question: Which team did Thierry Audel play for from 2007 to 2008?
Stepback Question: Which teams did Thierry Audel play for in his career

{question}


### Generate response query prompt
You are an advisor on tenancy rights. Below is some context related to tenancy rights:

{context}


You have received the below query from a tenant seeking to understand their rights.

{query}


The following stepback question is a summary of the essential question being asked by the tenant. Answer this question based on the context and original query provided. Answer in a conversational style.: 

{question}



Contact: christoph.rodgers@gmail.com