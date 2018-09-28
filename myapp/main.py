# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from bokeh.models.widgets import RangeSlider,Button,Div
from bokeh.io import curdoc,show
from bokeh.layouts import row,column, widgetbox,layout

import networkx as nx

from bokeh.models.graphs import from_networkx

from bokeh.models import StaticLayoutProvider,Circle,LabelSet,ColumnDataSource,CustomJS
from bokeh.plotting import figure
from numpy.core.multiarray import ndarray

df = pd.read_csv('myapp/data/pass_data.csv',encoding='utf-8')

passes=pd.DataFrame(df)

player=passes[['player_name','start_x','start_y','end_x','end_y','minute','second']]

player['game_seconds']=((player['minute']*60)+player['second'])
player.sort_values(["minute","second"],inplace=True)
pass_from=player.iloc[0::1,:]
pass_to= player.iloc[1::1,:]
pass_from.drop(pass_from.tail(1).index,inplace=True)


pass_player=pd.DataFrame()
pass_player['From']=pass_from['player_name'].values
pass_player['To']=pass_to['player_name'].values
pass_player['Game_Time_Start']=pass_from['game_seconds'].values
pass_player['Game_Time_End']=pass_to['game_seconds'].values
pass_player['Start_x']=pass_to['start_x'].values
pass_player['Start_y']=pass_to['start_y'].values
pass_player['End_x']=pass_to['end_x'].values
pass_player['End_y']=pass_to['end_y'].values

final_data=pass_player.groupby(['From','To','Game_Time_Start','Game_Time_End','Start_x','Start_y','End_x','End_y']).size().reset_index(name="Freq")


def player_plot():
    plot = figure(plot_height=500, plot_width=800,
                  tools="save,hover,tap,point_draw",
                  x_range=[0, 100], y_range=[0, 100], toolbar_location="below")
    plot.image_url(url=["myapp/static/images/base.png"], x=0, y=0, w=100, h=100, anchor="bottom_left")

    lower = np.round(range_slider.value[0])
    higher = np.round(range_slider.value[1])

    dummy = final_data[(final_data['Game_Time_Start']>=lower )& (final_data['Game_Time_Start']<=higher)]

    size = dummy.groupby(['From','To']).size().reset_index(name="Freq")

    grouped = dummy.groupby(['To'])[['Start_x','Start_y']].mean().reset_index()

    G = nx.DiGraph()

    for index, row in grouped.iterrows():
        # print row['From'],row[['Start_x','Start_y']]
        G.add_node(row['To'],pos=row[['Start_x','Start_y']])
        # G.add_edge(index,row['From'],weight=row['Freq'])

    for index, row in size.iterrows():

        G.add_edge(row['To'], row['From'],weight=row['Freq'])


    fixed_pos=grouped.set_index('To').T.to_dict('list')
    fixed_nodes = fixed_pos.keys()
    pos=nx.get_node_attributes(G,'pos')

    edges = G.edges()

    weights = [G[u][v]['weight'] for u,v in edges]


    graph = from_networkx(G,nx.spring_layout)
    fixed_layout_provider = StaticLayoutProvider(graph_layout=pos)
    graph.layout_provider = fixed_layout_provider


    graph.node_renderer.glyph = Circle(size=20,fill_color='orangered')

    plot.xgrid.grid_line_color = None
    plot.ygrid.grid_line_color = None
    plot.axis.visible=False
    graph.edge_renderer.data_source.data["line_width"] = [G.get_edge_data(a,b)['weight'] for a, b in G.edges()]
    graph.edge_renderer.glyph.line_width = {'field': 'line_width'}

    plot.renderers.append(graph)
    pos_values=np.array(fixed_pos.values())

    coordinates=pd.DataFrame(pos_values,columns=['x','y'])
    coordinates['player'] =fixed_pos.keys()
    source = ColumnDataSource(data=dict(x=coordinates.x,y=coordinates.y,player=coordinates.player))
    labels = LabelSet(x='x', y='y', text='player', source=source,x_offset=-45, y_offset=-25,text_color='black',render_mode='canvas',text_font_size='10pt')
    plot.renderers.append(labels)
    return plot

range_slider = RangeSlider(start=0, end=player.game_seconds.max(), value=(0,3600), step=1, title="Game Seconds",
                           callback_policy='mouseup',width=800)


def on_change(attr, old, new):
    layout.children[0] = player_plot()

for w in [range_slider]:
    w.on_change('value', on_change)
source_slider = ColumnDataSource(data=dict(value=[]))
source_slider.on_change('data', on_change)

range_slider.callback = CustomJS(args=dict(source=source_slider), code='source.data = { value: [cb_obj.value] }')

layout=column(player_plot(),range_slider)

curdoc().add_root(layout)
curdoc().add_root(source_slider)

curdoc().title = "Dynamic Network Pass Map"

