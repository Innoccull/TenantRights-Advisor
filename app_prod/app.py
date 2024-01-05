import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
from langchain.vectorstores.chroma import Chroma
from langchain.prompts import PromptTemplate
from langchain.embeddings.sentence_transformer import SentenceTransformerEmbeddings
from langchain.llms import HuggingFaceHub
from langchain.embeddings import VoyageEmbeddings
from dotenv import load_dotenv

#load environment variables
load_dotenv()

# Load vector database 
CHROMA_ADVICE_PATH = "chroma\\advice"

#embedding_function = SentenceTransformerEmbeddings(model_name="all-MiniLM-L6-v2")
embedding_function = VoyageEmbeddings()
advice_db = Chroma(persist_directory=CHROMA_ADVICE_PATH, embedding_function=embedding_function)

# Load generative AI model
model = HuggingFaceHub(repo_id="google/flan-t5-xxl", model_kwargs={"temperature": 0.5, "max_length": 512})

# Create prompt template
# Create prompt template
QUESTION_PROMPT_TEMPLATE = """
Below is some context related to tenancy rights:

{context}

---

Answer the below question succinctly based on the context provided. Provide a rationale for the answer provided.: {question}
"""

def get_response(input_text):
    # Process the input_text and generate the response
    advice_results = advice_db.similarity_search_with_relevance_scores(input_text, k=3)

    results = advice_results

    # If no context results, create prompt without additional context
    if len(results) == 0 or results[0][1] < 0.75:
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

        prompt_template = PromptTemplate.from_template(QUESTION_PROMPT_TEMPLATE)

        prompt = prompt_template.format(context=context_text, question=input_text)

        #call the model with the prompt
        response_text = model.predict(prompt)

    return response_text, advice_results

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.DARKLY])

app.layout = dbc.Container(
    fluid=True,
    children=[
        dbc.Row(
            dbc.Col(
                html.H1("Tenancy Helper", style={'color': 'white'}),
                width=12,
                className="mb-4 mt-4 text-center"
            )
        ),
        dbc.Row(
            [dbc.Col(
                dcc.Input(
                    id='input-text',
                    type='text',
                    value='',
                    placeholder='Enter your query here',
                    style={'width': '100%', 'margin': '0 auto', 'padding': '15px', 'fontSize': '18px', 'borderRadius': '5px', 'backgroundColor': '#2e2e2e', 'color': 'white', 'border': '1px solid #555'},
                ),
                width=10,
                className="mb-4 text-center"
            ),
            dbc.Col(
                dbc.Button(
                    html.Span("↓", style={'fontSize': '24px'}),
                    id='submit-button',
                    n_clicks=0,
                    color='light',
                    className='mb-4',
                    style={'width': '100%', 'margin': '0 auto', 'backgroundColor': 'white', 'color': 'black', 'border': 'none', 'padding': '10px', 'fontSize': '14px', 'cursor': 'pointer', 'display' : 'block','box-sizing' : 'border-box'}
                ),
                width=2,
                className="mb-4 text-center"
            )]
        ),
        dbc.Row(
            [
            dbc.Col(
                dbc.Card(
                dbc.CardBody(
                    [
                        html.H4("Answer"),
                        html.Div(id='output-text-container', style={'fontSize': '18px', 'color': 'white'})
                    ]
                ),
                style={'fontSize': '16px', 'color': 'white'}
            ),
            width=8,
            className="mb-4"
            ),
            dbc.Col(
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Sources"),
                            html.Ul([
                                html.Li(dcc.Link(id='card-1-link1', href='#', target='_blank', className='card-link')),
                                html.Li(dcc.Link(id='card-1-link2', href='#', target='_blank', className='card-link')),
                                html.Li(dcc.Link(id='card-1-link3', href='#', target='_blank', className='card-link'))
                            ]) 
                        ]
                    ),
                    style={'fontSize': '16px', 'color': 'white'},
                    id='card-1'
                ),
                width=4,
                className="mb-4"
            ),
            ],
        ),
    ]
)

@app.callback(
    [Output('output-text-container', 'children'),
     Output('card-1-link1', 'href'),
     Output('card-1-link2', 'href'),
     Output('card-1-link3', 'href')],
    [Input('submit-button', 'n_clicks')],
    [dash.dependencies.State('input-text', 'value')]
)
def update_output(n_clicks, input_text):
    if n_clicks > 0:  
        response, sources = get_response(input_text)

        # Extracting content and link data for each card
        card1_link1 = sources[0][0].metadata['link']
        card1_link2 = sources[1][0].metadata['link']
        card1_link3 = sources[2][0].metadata['link']
        
        
        return response, card1_link1, card1_link2, card1_link3
    else:
        return [], '', '', ''

if __name__ == '__main__':
    app.run_server(debug=True)