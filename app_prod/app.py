import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.llms import HuggingFaceHub
from langchain.embeddings import VoyageEmbeddings
from langchain_google_genai import GoogleGenerativeAI
from dotenv import load_dotenv

#load environment variables
load_dotenv()

# Load vector database 
CHROMA_ADVICE_PATH = "chroma\\advice"

#embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
embedding_function = VoyageEmbeddings()
advice_db = Chroma(persist_directory=CHROMA_ADVICE_PATH, embedding_function=embedding_function)

# Load generative AI model
# model = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature": 0.5, "max_length": 512})
model = GoogleGenerativeAI(model="gemini-pro")

conversation_history = []

# Create prompt template
QUESTION_PROMPT_TEMPLATE = """
You are an advisor on tenancy rights. Below is some context related to tenancy rights:

{context}

---

You have received the below query from a tenant seeking to understand their rights.

{query}

---

The following stepback question is a summary of the essential question being asked by the tenant. Answer this question based on the context and original query provided. Answer in a conversational style.: {question}
"""

SUMMARY_PROMPT_TEMPLATE = """

You are an advisor on tenancy rights. 
Your task is to step back and paraphrase a question from a tenant to a more generic step-back question so that is easier to answer in reference to tenancy law. 

Here are a few examples:
Original Question: Which position did Knox Cunningham hold from May 1955 to Apr 1956?
Stepback Question: Which positions have Knox Cunning- ham held in his career?

Original Question: Who was the spouse of Anna Karina from 1968 to 1974?
Stepback Question: Who were the spouses of Anna Karina?

Original Question: Which team did Thierry Audel play for from 2007 to 2008?
Stepback Question: Which teams did Thierry Audel play for in his career
---

{question}
"""

# Function to get a refined query
def get_refined_query(input_text):

    prompt_template = PromptTemplate.from_template(SUMMARY_PROMPT_TEMPLATE)
    prompt = prompt_template.format(question = input_text)

    refined_query = model.invoke(prompt)

    return (refined_query)

# Function to get a response to a user's query
def get_response(input_text, orig_query):
    # Process the input_text and generate the response
    advice_results = advice_db.similarity_search_with_relevance_scores(input_text, k=3)

    results = advice_results

    # If no context results, create prompt without additional context
    if len(results) == 0 or results[0][1] < 0.75:
        response_text = "That is not a question that I was able to find a reliable answer for. Try rewording your question or you may check out the articles below to see if they answer your query."
        prompt = "No prompt sent"
    else:
    # If there are context results, create prompt with the context results included
        
        # Get sources for the results
        sources = [doc[0].metadata['source'] for doc in results]

        # Get the complete text for the source result
        raw_source_text = []

        for source in sources:
            with open (source, 'r', encoding='utf-8') as file:
                article = file.read()
                raw_source_text.append(article)
            file.close()

        #sources_text = "\n\n---\n\n".join([source for source in raw_source_text])

        context_text = "\n\n---\n\n".join([doc.page_content for doc, _score in results if _score > 0.75])

        # Create prompt with context
        prompt_template = PromptTemplate.from_template(QUESTION_PROMPT_TEMPLATE)
        prompt = prompt_template.format(context=raw_source_text[0], question=input_text, query=orig_query)

        print(prompt)

        # Call the model with the prompt
        response_text = model.invoke(prompt)

    return response_text, advice_results

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            dbc.Col(
                html.H1("TenantRights Advisor", style={'color': 'white'}),
                width=12,
                className="mb-4 mt-4 text-center"
            )
        ),
        dbc.Row(
            [
            dbc.Col(
                width=2
            ),          
            dbc.Col(
                dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Original question"),
                        html.Div(id='original-query-container')
                    ]
                ),
            ),
            width=7,
            className="mb-4"
            ),
            dbc.Col(
                width=3
            )
            ],
            style={'display': 'none'},
            id='original-query-row'
        ),
        dbc.Row(
            [
            dbc.Col(
                width=2
            ),          
            dbc.Col(
                dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Refined questions"),
                        html.Div(id='refined-query-container', 
                                 style={'fontSize': '18px', 'color': 'white'})
                    ]
                ),
                style={'fontSize': '16px', 'color': 'white'}
            ),
            width=7,
            className="mb-4"
            ),
            dbc.Col(
                width=3
            )
            ],
            style={'display': 'none'},
            id='refined-query-row'
        ),
        dbc.Row(
            [
            dbc.Col(
                width=2
            ),          
            dbc.Col(
                dbc.Card(
                dbc.CardBody(
                    [
                        html.H5("Answer"),
                        html.Div(id='output-text-container', 
                                 style={'fontSize': '18px', 'color': 'white'})
                    ]
                ),
                style={'fontSize': '16px', 'color': 'white'}
            ),
            width=7,
            className="mb-4"
            ),
            dbc.Col(
                width=3
            )
            ],
            style={'display': 'none'},
            id='answer-row'
        ),
        dbc.Row(
            [
            dbc.Col(
                width=2
            ),
            dbc.Col(
                [
                html.H5("Sources"),
                dbc.Card(
                    dbc.ListGroup(
                        [
                            dbc.ListGroupItem(dcc.Link(id='card-1-link1', href='#', target='_blank', className='card-link')),
                            dbc.ListGroupItem(dcc.Link(id='card-1-link2', href='#', target='_blank', className='card-link')),
                            dbc.ListGroupItem(dcc.Link(id='card-1-link3', href='#', target='_blank', className='card-link')),
                        ],
                        flush=True,
                    ),
                    style={'fontSize': '16px', 'color': 'white'},
                    id='card-1'
                )],
                width=4,
                className="mb-4"
            ),
            dbc.Col(
                width=4
            )
            ],
            style={'display': 'none'},
            id='source-row'
        ),
        dbc.Row(
            [
            dbc.Col(width=2),   
            dbc.Col(
                dcc.Input(
                    id='input-text',
                    type='text',
                    value='',
                    placeholder='Enter your tenancy related query here',
                    style={'width': '100%', 'margin': '0 auto', 'padding': '15px', 'fontSize': '18px', 'borderRadius': '5px', 'backgroundColor': '#2e2e2e', 'color': 'white', 'border': '1px solid #555'},
                ),
                width=7,
                className="mb-4 text-center"
            ),
            dbc.Col(
                dbc.Button(
                    html.Span("↑", style={'fontSize': '24px'}),
                    id='submit-button',
                    n_clicks=0,
                    color='light',
                    className='mb-4',
                    style={'width': '100%', 'margin': '0 auto', 'backgroundColor': 'white', 'color': 'black', 'border': 'none', 'padding': '10px', 'fontSize': '14px', 'cursor': 'pointer', 'display' : 'block','box-sizing' : 'border-box'}
                ),
                width=1,
                className="mb-4 text-center"
            ),
            dbc.Col(width=2)]
        ),
    ]
)

@app.callback(
    [Output('output-text-container', 'children'),
     Output('card-1-link1', 'href'),
     Output('card-1-link2', 'href'),
     Output('card-1-link3', 'href'),
     Output('original-query-container', 'children'),
     Output('refined-query-container', 'children'),
     Output('original-query-row', 'style'),
     Output('refined-query-row', 'style'),
     Output('answer-row', 'style'),
     Output('source-row', 'style')
     ],
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('input-text', 'value')]
)
def update_output(n_clicks, input_text):
    hide_style = {'fontSize': '18px', 'color': 'white', 'display': 'none'}

    if n_clicks > 0:

        conversation_history.append(input_text)

        refined_query = get_refined_query(input_text)
        response, sources = get_response(refined_query, input_text)

        conversation_history.append(response)

        # Extracting content and link data for each card
        card1_link1 = sources[0][0].metadata['link']
        card1_link2 = sources[1][0].metadata['link']
        card1_link3 = sources[2][0].metadata['link']
        
        display_style = {'fontSize': '18px', 'color': 'white', 'display': 'flex'} 

        return response, card1_link1, card1_link2, card1_link3, input_text, refined_query, display_style, display_style, display_style, display_style
    else:
        return [], '', '', '', '', '', hide_style, hide_style, hide_style, hide_style

if __name__ == '__main__':
    app.run_server(debug=True)