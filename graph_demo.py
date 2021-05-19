import dash
import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
import dash_table as dt
import dash_cytoscape as cyto
from tweepy_helper import get_tweets
from dash.dependencies import Input, Output, State
from plotly.offline import init_notebook_mode
import numpy as np

init_notebook_mode(connected=True)

# External script
external_scripts = ['https://cdnjs.cloudflare.com/ajax/libs/animejs/2.0.2/anime.min.js']
# Explore external_stylesheets themes here https://dash-bootstrap-components.opensource.faculty.ai/docs/themes/explorer/
app = dash.Dash(external_stylesheets=[dbc.themes.SOLAR], external_scripts=external_scripts)

# Define app layout, using Dash Bootstrap Components https://dash-bootstrap-components.opensource.faculty.ai/docs/
app.layout = dcc.Tabs([
    dcc.Tab(label="Interactive Graph", children=[
        dbc.Container(
            [
                html.H1("Twitter Analysis Demo", className="ml12"),
                dbc.Row([
                    dbc.Col(dbc.FormGroup(
                        [
                            dbc.Label("Search Phrase", html_for="search_phrase"),
                            dbc.Input(
                                id="search_phrase", placeholder="Enter a search phrase...", type="text", debounce=True),
                            html.Br(),
                            html.P(id='cytoscape-tapNodeData-json'),
                            html.Br(),
                            html.P(id='cytoscape-tapEdgeData-output'),

                        ]
                    ), md=2),

                    dbc.Col(
                        cyto.Cytoscape(
                            id='cytoscape',
                            layout={'name': 'cose'},
                            style={'width': '100%', 'height': '800px'},
                            elements=[],
                            stylesheet=[
                                # See https://js.cytoscape.org/#style
                                # Colour nodes by sentiment, size by support
                                {
                                    'selector': 'node',
                                    'style': {
                                        'label': 'data(label)',
                                        'font-size': 6,
                                        'background-color': 'mapData(weight, -1, 1, red, green)',
                                        "width": 'data(size)',
                                        "height": 'data(size)',
                                        "opacity": 0.75,
                                        "color": "white"
                                    },
                                }, {
                                    'selector': 'edge',
                                    'style': {
                                        'width': 0.5
                                    }
                                },
                            ]
                        ), md=10)])],
            fluid=True)]
            ),

    dcc.Tab(label="Statistics", children=[
        html.Div(id="table1"),
        # html.Div(id="top_tweets"),
        # html.Div(id="places"),
        html.Div(className="stats",
                 children=[html.H2("Summary of tweets sentiment"),
                           dcc.Graph(id="histogram")]),
        html.Div(className="stats",
                 children=[html.H2("Word cloud"),
                           html.Img(className="word_cloud", src="/assets/cloud.png")])
    ])
]
)


@app.callback(
    # Callback to update graph elements, based on a search phrase
    Output("cytoscape", "elements"),
    Output("table1", "children"),
    # Output("places", "children"),
    # Output("top_tweets", "children"),
    Output("histogram", "figure"),
    Input("search_phrase", "value"),
    prevent_initial_call=True)
def update_graph(search_phrase):
    # User defines number of tweets and search string

    node_df, edge_df, place_df, hist_fig = get_tweets(search_phrase, 50)

    node_df["sentiment"] = node_df["sentiment"] * 100

    elements = []
    counts = node_df.groupby(by='tag').count()

    avg_sentiment = node_df.groupby(by='tag').mean()

    # Add nodes
    for tag in node_df['tag'].unique():
        node = {
            'data': {'id': tag,
                     'label': tag,
                     # A scaling factor is applied to each node here.
                     'size': int(counts.loc[tag]) * 3,
                     'count': counts.loc[tag],
                     'weight': float(avg_sentiment.loc[tag])
                     }
        }
        elements.append(node)
    # Add edges
    edge_count = edge_df.groupby(['tag', 'associated_tag']).size().reset_index(name="pair_count")

    for pair in edge_count.index:
        edge = {'data': {
            'source': edge_count.loc[pair, 'tag'], 'target': edge_count.loc[pair, 'associated_tag'],
            "count": edge_count.loc[pair, 'pair_count']}}
        if edge not in elements:
            elements.append(edge)

    # table data frame
    table_df = place_df.copy()
    table_df = table_df.rename(columns={'place': 'Location'})
    table_df["Location"].replace("", np.nan, inplace=True)
    table_df = table_df.dropna().groupby("Location").count().sort_values(by="tweet", ascending=False).head()
    table_df = table_df.reset_index()
    top_five = node_df.groupby("tag").count().sort_values(by="sentiment", ascending=False).head()
    top_five = top_five.reset_index()
    top_five.columns = ["Tag", "Count"]
    table_df["Hashtag"] = top_five["Tag"]
    table_df = table_df.drop(['tweet'], axis=1)

    table_div = html.Div(className="stats",
                         children=[html.H2("The TOP 5"),
                                   dt.DataTable(
                                       style_header={
                                           'whiteSpace': 'normal',
                                           'backgroundColor': '#E1E8ED',
                                           'fontWeight': 'bold',
                                           'color': '#484848'},
                                       style_cell={
                                           'textAlign': 'center'
                                       },
                                       id="table1",
                                       columns=[{'name': i, 'id': i} for i in table_df.columns],
                                       data=table_df.to_dict("rows"))])

    # calc for place table
    # place_df["place"].replace("", np.nan, inplace=True)
    # place_head = place_df.dropna().groupby("place").count().sort_values(by="tweet", ascending=False).head()
    # place_head = place_head.reset_index()
    # place_columns = [{'name': i, 'id': i} for i in place_head.columns]
    # place_div = html.Div(className="stats",
    #                      children=[html.H2("The top 5 places these tweets came from"),
    #                                dt.DataTable(
    #                                    style_header={'whiteSpace': 'normal',
    #                                                  'backgroundColor': '#1DA1F2',
    #                                                  'textAlign': 'center'},
    #                                    id="place_table",
    #                                    columns=place_columns,
    #                                    data=place_head.to_dict("rows"))])
    #
    # Calc for top 5 tweets
    # top_five = node_df.groupby("tag").count().sort_values(by="sentiment", ascending=False).head()
    # top_five = top_five.reset_index()
    # top_five.columns = ["Tag", "Count"]
    # top_five_cols = [{'name': i, 'id': i} for i in top_five.columns]
    # top_5_div = html.Div(className="stats",
    #                      children=[html.H2("The top 5 hashtags"),
    #                                dt.DataTable(style_header={'whiteSpace': 'normal',
    #                                                           'backgroundColor': '#E1E8ED',
    #                                                           'textAlign': 'center',
    #                                                           'maxWidth': 0,
    #                                                           'overflowX': 'auto',
    #                                                           },
    #                                             id="top_five_table",
    #                                             columns=top_five_cols,
    #                                             data=top_five.to_dict("rows"))])
    return elements, table_div, hist_fig


@app.callback(Output('cytoscape-tapEdgeData-output', 'children'),
              Input('cytoscape', 'tapEdgeData'))
def displayTapEdgeData(data):
    if data:
        return "You recently clicked/tapped the edge between " + data['source'].upper() + " and " + data[
            'target'].upper() + " which occured {} times.".format(data['count'])


@app.callback(Output('cytoscape-tapNodeData-json', 'children'),
              Input('cytoscape', 'tapNodeData'))
def displayTapNodeData(data):
    return "#{} was tweeted {} times with an average sentiment of {}".format(data["label"], data["count"],
                                                                             data["weight"] / 100)


if __name__ == "__main__":
    app.run_server()
