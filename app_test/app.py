from dash import Dash, html, dcc, callback, Output, Input, State
from dash.exceptions import PreventUpdate
import dash_bootstrap_components as dbc
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.llms import HuggingFaceHub
from langchain.embeddings import VoyageEmbeddings
import os
from dotenv import load_dotenv
from langchain_google_genai import GoogleGenerativeAI

#load environment variables
load_dotenv()

# Load vector database 
CHROMA_ADVICE_PATH = "app_test\\chroma\\advice"

#embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
embedding_function = VoyageEmbeddings()
advice_db = Chroma(persist_directory=CHROMA_ADVICE_PATH, embedding_function=embedding_function)


# Load generative AI model
# model = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature": 0.5, "max_length": 512})
model = GoogleGenerativeAI(model="gemini-pro")

# Create prompt template
QUESTION_PROMPT_TEMPLATE = """
You are an advisor on tenancy rights. Below is some context related to tenancy rights:

{context}

---

You have received the below query from a tenant seeking to understand their rights.

{query}

---

The following stepback question is a summary of the essential question being asked by the tenant. Answer this question based on the context and original query provided. Provide the answer as a conversational response.: {question}
"""

SUMMARY_PROMPT_TEMPLATE = """

You are an advisor on tenancy rights. 
Your task is to step back and paraphrase a question from a tenant to a more generic step-back question so that is easier to answer in reference to tenancy law. 


Here are a few examples:
Original Question: Which position did Knox Cunningham hold from May 1955 to Apr 1956?
Stepback Question: Which posiYou are an advisor on tenancy rights. 
Your task is to step back and paraphrase a question from a tenant to a more generic step-back question so that is easier to answer in reference to tenancy law. 


Here are a few examples:
Original Question: Which position did Knox Cunningham hold from May 1955 to Apr 1956?
Stepback Question: Which positions have Knox Cunning- ham held in his career?

Original Question: Who was the spouse of Anna Karina from 1968 to 1974?
Stepback Question: Who were the spouses of Anna Karina?

Original Question: Which team did Thierry Audel play for from 2007 to 2008?
Stepback Question: Which teams did Thierry Audel play for in his career
---

{question}tions have Knox Cunning- ham held in his career?

Original Question: Who was the spouse of Anna Karina from 1968 to 1974?
Stepback Question: Who were the spouses of Anna Karina?

Original Question: Which team did Thierry Audel play for from 2007 to 2008?
Stepback Question: Which teams did Thierry Audel play for in his career
---

{question}
"""

# Advice directory
summaries_directory = "data//aratohu_summaries//"


# Dash application
app = Dash(external_stylesheets=[dbc.themes.BOOTSTRAP],suppress_callback_exceptions=True)

app.layout = html.Div([
    html.H1(children='Tenancy Helper', style={'textAlign':'center'}),
    dbc.Row(
            [
                dbc.Col(html.Div(children = 
                                 [
                                html.H1("Query"),
                                html.P("Original query text"),
                                dbc.Textarea(id='raw_query', className="mb-3", placeholder="Query", style={"height" : "200px"}), 
                                html.P('Summary Prompt'),
                                dbc.Textarea(id='summary_prompt', className="mb-3", value="Provide a summary of the following:", style={"height" : "200px"}),
                                dbc.Select(id='summarise', 
                                           options=[
                                                {'label': 'Yes', 'value': 1},
                                                {'label': 'No', 'value': 2}
                                           ],
                                           value=2),
                                html.Br(),
                                dbc.Button("Generate query", id='btn_sum_query', color="primary", className="me-1"),
                                html.Br(),
                                html.Br(),
                                html.P(),
                                html.Div("", id='sum_query_text')
                                 ]), 
                                 width=4,
                                 style={"border":"0.5px black solid"}),
                dbc.Col(children = [
                    html.H1("Prompt and Response"),
                    html.P("Prompt template"),
                    dbc.Textarea(id='query_prompt', className="mb-3", value=QUESTION_PROMPT_TEMPLATE, style={"height" : "200px"}),
                    html.Br(),
                    dbc.Button("Get response", id='btn_get_response', color="primary", className="me-1"),
                    html.Br(),
                    html.Br(),
                    html.P("Response"),
                    html.Div("", id='answer')
                    ],
                    style={"border":"1px black solid"}),
                dbc.Col(children=[
                    html.H1("Sources"),
                    html.Div("Relevant advice", id='relevant_advice'),
                    html.P("Prompt"),
                    html.Div("", id="full_query_prompt")
                    ], 
                    width=4,
                    style={"border":"1px black solid"}),
            ]
        )

])

@callback(
    Output('sum_query_text', 'children'),
    [Input('btn_sum_query', 'n_clicks'),
     Input("summarise", 'value')],
    [State(component_id='raw_query', component_property='value'),
     State(component_id='summary_prompt', component_property='value')]
)
def get_summary(n_clicks, summarise, input_value, summary_prompt):

    if(n_clicks is None):
        raise PreventUpdate

    if(input_value is None):
        return ""
    elif(summarise == '1'):
        SUMMARY_PROMPT_TEMPLATE = summary_prompt +  " {question} "
        prompt_template = PromptTemplate.from_template(SUMMARY_PROMPT_TEMPLATE)
        prompt = prompt_template.format(question = input_value)

        query_text = model.predict(prompt)
        return query_text
    else:
        return input_value
    
@callback(
    [Output('answer', 'children'),
     Output('full_query_prompt', 'children'),
     Output('relevant_advice', 'children')],
    [Input('btn_get_response', 'n_clicks')],
    [State('sum_query_text', 'children'),
     State(component_id='raw_query', component_property='value'),
     State('query_prompt', 'value')]
)
def get_answer(n_clicks, input_value, raw_query, query_prompt):

    if(n_clicks is None):
        raise PreventUpdate

    if(input_value is None):
        return ""
    else:
        advice_results = advice_db.similarity_search_with_relevance_scores(input_value, k=3)

        results = advice_results

        # If no context results, create prompt without additional context
        if len(results) == 0 or results[0][1] < 0.70:
            response_text = "That is not a question that I was able to find a reliable answer for. Try rewording your question or you may check out the articles below to see if they answer your query."
            prompt = "No prompt sent"
        else:
        # If there are context results, create prompt with the context results included
            
            sources = [doc[0].metadata['source'] for doc in results]

            raw_source_text = []

            for source in sources:
                with open (source, 'r', encoding='utf-8') as file:
                    article = file.read()
                    raw_source_text.append(article)
                file.close()

            #sources_text = "\n\n---\n\n".join([source for source in raw_source_text])

            context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results if _score > 0.75])

            prompt_template = PromptTemplate.from_template(query_prompt)
            prompt = prompt_template.format(context=raw_source_text[0], question=input_value, query=raw_query)

            print(prompt)

            response_text = ""

            #call the model with the prompt
            response_text = model.invoke(prompt)

        cards = [
        dbc.Col(
            dbc.Card(
                [
                    html.P(f"Content: {item[0].page_content}", className="card-text", style={'color': 'black', 'padding': '5px'}),
                    html.P(f"Source: {item[0].metadata['source']}", className="card-text", style={'color': 'black', 'padding': '5px'}),
                    html.P(f"Link: {item[0].metadata['link']}", className="card-text", style={'color': 'black', 'padding': '5px'}),
                    html.P(f"Score: {item[1]}", className="card-text", style={'color': 'black', 'padding': '5px'}),
                ],  # Set text color to black
                color="light",
                inverse=True,
                style={'margin': '10px'}  # Add some margin to the card
            )
        ) for item in results
    ]
        return (response_text, prompt, cards)


if __name__ == '__main__':
    app.run(debug=True)