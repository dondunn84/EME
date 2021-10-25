from datetime import datetime
import numpy as np
import pandas as pd
from visualizations import mk_offs
from bokeh.events import SelectionGeometry, Tap, DoubleTap
from bokeh.models import CustomJS, Label, NumberFormatter, LabelSet, ColorBar, LinearColorMapper, EqHistColorMapper, CategoricalColorMapper, Range1d, ColumnDataSource, BasicTickFormatter, Band, BoxEditTool, DataTable, TableColumn, HoverTool, BoxSelectTool, LabelSet, Rect, CDSView, GroupFilter, DatetimeTickFormatter, Quad, Circle
from bokeh.palettes import Spectral3
from bokeh.models.widgets import Panel, Tabs, Button, TextInput, Div
from bokeh.plotting import figure, output_file, show
from bokeh.layouts import row, column, layout, gridplot
from bokeh.transform import linear_cmap
from bokeh.models.filters import CustomJSFilter
from bokeh.io import curdoc
import sig_detect as sd


class TraceSet:
    
    def __init__(self, df, lvl_line):
        self.num_datapoints = len(df['lvls'][0])
        self.num_traces = len(df['lvls'])
        self.lvls = np.array(df['lvls'].tolist())
        self.start_frq = df['start_frq'][0]
        self.stop_frq = df['stop_frq'][0]
        self.step_frq = (self.stop_frq - self.start_frq)/self.num_datapoints
        self.start_time = str(df['timestamp'].min().round(freq = 'S'))[:-6]
        self.stop_time = str(df['timestamp'].max().round(freq = 'S'))[:-6]
        self.timestamps = np.array(df['timestamp'].tolist())
        self.offs = np.array(mk_offs(self.start_frq, self.step_frq, self.num_datapoints, self.num_traces))
        self.maximum = np.max(self.lvls, axis=0)
        self.minimum = np.min(self.lvls, axis=0)
        self.mean = np.mean(self.lvls, axis=0)
        self.x_min = self.offs.min()/1000000
        self.x_max = self.offs.max()/1000000
        self.xrange = Range1d((self.x_min), (self.x_max), bounds="auto")
        self.y_min = self.lvls.min()
        self.y_max = self.lvls.max()
        self.yrange = Range1d(self.y_min, self.y_max+10, bounds="auto")
        self.z_min=df['timestamp'].min()
        self.z_max=df['timestamp'].max()
        self.lvl_line = lvl_line
        self.source = ColumnDataSource(data=dict(x=[], y=[], width=[], height=[], start_frq=[], stop_frq=[], pwr=[], name=[], foi=[], color=[], trans=[]))
        self.foi_master_cds = ColumnDataSource(data=dict(name=['default'], color=['firebrick'], trans=[0.25]))
        self.sweep_hist_cds = ColumnDataSource(dict(bottom=np.full(
            shape=self.num_datapoints,
            fill_value=self.y_min,
            dtype=np.int
        ), top=self.lvls[0], left=self.offs[0]/1000000, right=(self.offs[0]/1000000 + self.step_frq/1000000)))
        self.sweep_cds = ColumnDataSource(dict(timestamp=[self.timestamps[0]], index=[0], start_index=[0], stop_index=[0], last_timestamp=[self.timestamps[0]], intervals=[None]))
        self.sweep_timestamp = self.sweep_cds.data['timestamp'][0]
        self.sweep_index = self.sweep_cds.data['index'][0]
        
   
    def spec_histogram(self):
        

        xbin = int(self.num_datapoints)
        ybin = int(self.lvls.max()-self.lvls.min())*2
        bins = (ybin,xbin)
        h, xe, ye = np.histogram2d(self.lvls.flatten(), self.offs.flatten(), bins=bins)
        
        #setup plot
        p1 = figure(plot_width=1250,
               plot_height=300,
               tooltips=[("x", "$x{0.000}"), ("y", "$y"), ("value", "@image")],
               tools=['box_zoom', 'pan', 'reset', 'save'],
               x_range=self.xrange, 
               x_axis_type='linear',
               y_range=self.yrange, 
               title=f'Freq Range:{round(self.start_frq/1000000, 3)} - {round(self.stop_frq/1000000, 3)}MHz, Time Period: {self.start_time} - {self.stop_time}, RBW: {round(self.step_frq/1000, 3)}kHz, Number of Traces: {self.num_traces}')
        vmax = ((self.num_datapoints * self.num_traces) / 25000 )
        color_mapper = EqHistColorMapper(palette='Turbo256', low=8, high=vmax)
        p1.xaxis[0].formatter = BasicTickFormatter(use_scientific = False)
        p1.image(image=[h],
                x=(self.x_min),
                y=(self.y_min),
                dw=[(self.x_max-self.x_min)],
                dh=[(self.y_max-self.y_min)],
                color_mapper=color_mapper)
        #p1.line(x[0:num_datapoints], maximum, line_width=4, level='overlay')
        p1.xaxis.axis_label = 'Frequency (MHz)'
        p1.yaxis.axis_label = 'Power (dBm)'
        p1.xaxis.axis_label_text_font_size = "10pt"
        p1.yaxis.axis_label_text_font_size = "10pt"
        p1.yaxis.axis_label_text_font = "arial"
        p1.yaxis.axis_label_text_font = "arial"
        p1.xaxis.axis_label_text_font_style = "bold"
        p1.yaxis.axis_label_text_font_style = "bold"
        
        upper = []
        for i in self.maximum:
            upper.append(self.y_max+10)
        lower = []
        for i in self.minimum:
            lower.append(self.y_min)
        x_values = []
        for i in self.offs[0]:
            x_values.append(i/1000000)

        fill_above = {'x_values': x_values,
                    'lower': self.maximum,
                    'upper': upper}
        fill_below = {'x_values': x_values,
                    'lower': lower,
                    'upper': self.minimum}

        source2 = ColumnDataSource(fill_above)
        source3 = ColumnDataSource(fill_below)
        
        band = Band(base='x_values', lower='lower', upper='upper', source=source2, 
                level='annotation', fill_color='#414a4c', fill_alpha=1.0, line_width=1, line_color='black')
        band2 = Band(base='x_values', lower='lower', upper='upper', source=source3, 
                level='annotation', fill_color='silver', fill_alpha=1.0, line_width=1, line_color='black')
        p1.add_layout(band)
        p1.add_layout(band2)
        
        js_code = """
    
        var geometry = cb_obj['geometry'];
        var data = source.data
        var foi_data = source2.data
        var foi_data_index = parseInt(source2.selected.indices)
        var name = "Name"
        var y_range_start = p1.y_range.start
        var x_0 = geometry['x0']
        var x_1 = geometry['x1']
        var y_1 = geometry['y1']
        var width = geometry['x1'] - geometry['x0']
        var height = geometry['y1'] - y_range_start
        var x = geometry['x0'] + width / 2
        var y = y_range_start + height / 2
        var foi = foi_data['name'][foi_data_index]
        if (!foi) {
        foi = 'default'
        }
        
        var color = 'firebrick'
        var trans = 0.25
        
        for (let i = 0; i <= data['name'].length; i++) {
            if (foi == foi_data['name'][foi_data_index]) {
                console.log(foi_data['name'][foi_data_index]);
                color = foi_data['color'][foi_data_index];
                trans = foi_data['trans'][foi_data_index];
            }
        }
        
    
        data['x'].push(x)
        data['y'].push(y)
        data['width'].push(width)
        data['height'].push(height)
        data['start_frq'].push(x_0)
        data['stop_frq'].push(x_1)
        data['pwr'].push(y_1)
        data['name'].push(name)
        data['color'].push(color)
        data['trans'].push(trans)
        data['foi'].push(foi)

        source.change.emit()
        """

        labels = LabelSet(x="start_frq", y="pwr", y_offset=5, text='name', text_font_size='8pt', source=self.source, text_color='white')
        
        frq_select = BoxSelectTool(description='Freq Highlighter')
        p1.add_tools(frq_select)

        callback = CustomJS(args=dict(source=self.source, source2=self.foi_master_cds, p1=p1), code=js_code)

        gly = p1.rect(x='x', y='y', width='width', height='height', line_color='white', fill_alpha='trans', fill_color='color', source=self.source, level='overlay')

        frq_edit = BoxEditTool(renderers=[gly])
        
        max_line = p1.line(x=x_values, y=self.maximum, line_width=2, color='red', alpha=0.7, legend_label='Max', level='overlay')
        avg_line = p1.line(x=x_values, y=self.mean, line_width=2, color='black', alpha=0.7, legend_label='Avg', level='overlay')
        min_line = p1.line(x=x_values, y=self.minimum, line_width=2, color='yellow', alpha=0.7, legend_label='Min', level='overlay')

        
        p1.legend.location = "top_left"
        p1.legend.click_policy="hide"
        
        p1.add_tools(frq_edit)
        p1.js_on_event(SelectionGeometry, callback)

        p1.add_layout(labels)
        p1.toolbar.logo = None
        
        return p1
    
    def waterfall(self):
        tooltips=[ ("y", "$y{0.00}"), ]
        hover_tool = HoverTool(tooltips=[('freq', "$x{0.000}"), ('time', '$y{%H:%M:%S}'), ("power", "@image")], formatters={'$y': 'datetime'})
        color_mapper = LinearColorMapper(palette="Turbo256", low=self.y_min, high=self.y_max)
        
        p2 = figure(plot_width=1250,
                    plot_height=300,
                    x_range=self.xrange,
                    y_range=Range1d(self.z_min, self.z_max, bounds="auto"),
                    tools=('box_zoom', 'pan', 'xpan', 'ypan', 'reset', 'save'))
        p2.image(image=[self.lvls], color_mapper=color_mapper,
                   dh=[(self.z_max-self.z_min)], dw=[(self.x_max-self.x_min)], x=[self.x_min], y=[self.z_min])
        p2.toolbar.logo = None
        #tools=('box_edit', 'box_select', 'box_zoom', 'pan', 'xpan', 'ypan', 'reset', 'save')
        p2.yaxis.formatter = DatetimeTickFormatter(seconds=["%H:%M:%S"],
                                            minutes=["%H:%M:%S"],
                                            minsec=["%H:%M:%S"],
                                            hours=["%H:%M:%S"])
        #print(self.z_max.strftime("%m/%d/%Y, %H:%M:%S"), self.zmin.strftime("%m/%d/%Y, %H:%M:%S"))
        p2.add_tools(hover_tool)
        
        js_code4 = """
            var data = cb_obj
            var y = cb_obj.y
            var x = cb_obj.x
            var sy = cb_obj.sy
            var sx = cb_obj.sx
            var timestamps = source2
            var chart_data = source3.data
            var chart_y = chart_data['top']
            let intervals = source4.data['intervals']
            let time = source4.data['timestamp']
            
            clearInterval(intervals[0]);
            
            for (let i = 0; i < timestamps.length; i++) {
                var value = y - timestamps[i]
                if(value <= 0){
                    var index = i;
                    break;
                }
                }
            
            source4.data['index'].shift()
            source4.data['index'].push(index)
            source4.data['timestamp'].shift()
            source4.data['timestamp'].push(timestamps[index+1])
            source4.data['last_timestamp'].shift()
            source4.data['last_timestamp'].push(timestamps[index])
            source3.data['top'] = source[index];
            var date = new Date(Math.round(source4.data['timestamp']));
            var time_str = date.toUTCString();
            ti.text = time_str + ", Trace Number: " + index.toString()
            
            ti.change.emit()
            source3.change.emit();
            source4.change.emit();
        """
        
        js_code5 = """
        var count = source4.data['index'] - 1;
        let intervals = source4.data['intervals']
        let sw_idx = source4.data['index']
        let sw_timestamp = source4.data['timestamp']
        let sw_last_timestamp = source4.data['last_timestamp']
        
        console.log(intervals);
        clearInterval(intervals[0]);
        intervals.shift();
        
        console.log(intervals)
        var interval = setInterval(foo, 100)
        intervals.push(interval)
        source4.change.emit();
        console.log(intervals)
        
        function foo() {
            if (count >= source.length){
            clearInterval(interval)
            return;
            }
            sw_last_timestamp.shift();
            sw_last_timestamp.push(sw_timestamp[0]);
            sw_idx.shift();
            sw_idx.push(count);
            sw_timestamp.shift();
            sw_timestamp.push(source5[count]);
            source2.data['top'] = source[count];
            var date = new Date(Math.round(sw_timestamp));
            var time_str = date.toUTCString();
            ti.text = time_str + ", Trace Number: " + count.toString()
            ti.change.emit();
            source2.change.emit();
            source4.change.emit();
            count++;
            }
            
        
        """
        div_timestamp = Div(text="""Sweep Histogram""", align='center')
        
        callback5 = CustomJS(args=dict(source=self.lvls, source2=self.sweep_hist_cds, source4=self.sweep_cds, source5=self.timestamps, ti=div_timestamp), code=js_code5)
        
        p2.js_on_event(DoubleTap, callback5)
        
        callback4 = CustomJS(args=dict(source=self.lvls, source2=self.timestamps, source3=self.sweep_hist_cds, source4=self.sweep_cds, ti=div_timestamp), code=js_code4)
        
        p2.js_on_event(Tap, callback4)
        sweep_circle = Circle(x=self.x_min, y="timestamp", size=3, line_color="black", fill_color="white", line_width=3)
        
        
        sweep_quad = Quad(top="timestamp", bottom="last_timestamp", left=self.x_min, right=self.x_max)
        p2.add_glyph(self.sweep_cds, sweep_quad)
        
        
        return p2, div_timestamp
    
    def sweep_histogram(self):
        curdoc().theme = 'contrast'
        #output_file("msn-hist_sweep.html")
        

        p3 = figure(plot_height = 300, plot_width = 1250,
                   title = None,
                   x_axis_label = 'Frequency (MHz)', 
                   y_axis_label = 'Power (dbm)',
                   tools=['box_zoom', 'pan', 'reset', 'save', 'hover'],
                   y_range=self.yrange,
                   x_range=self.xrange
                   )

        mapper = linear_cmap(field_name='top', palette='Turbo256', low=self.y_min, high=self.y_max)

        # Add a quad glyph
        glyph = Quad(left="left", right="right", top="top", bottom="bottom", fill_color=mapper, line_color=None)
        p3.add_glyph(self.sweep_hist_cds, glyph)
        p3.toolbar.logo = None
        
        return p3
    
    def data_table(self):
        columns = [
            TableColumn(field="name", title="Name"),
            TableColumn(field="width", title="Bandwidth", formatter=NumberFormatter(format="0.000", rounding='floor')),
            TableColumn(field="x", title="Center Freq", formatter=NumberFormatter(format="0.000", rounding='floor')),
            TableColumn(field="start_frq", title="Start Freq", formatter=NumberFormatter(format="0.000", rounding='floor')),
            TableColumn(field="stop_frq", title="Stop Freq", formatter=NumberFormatter(format="0.000", rounding='floor')),
            TableColumn(field="pwr", title="Power", formatter=NumberFormatter(format="0.0", rounding='floor')),
            TableColumn(field="foi", title="FOI"),
            TableColumn(field="color", title="Color"),
            TableColumn(field="trans", title="Transparency"),
            ]
        
        columns2 = [
            TableColumn(field="name", title="Name"),
            TableColumn(field="color", title="Color"),
            TableColumn(field="trans", title="Transparency")
        ]
        text_select_foi = TextInput(value="default", title="Current FOI:", disabled=True)
        
        gf = GroupFilter(column_name='foi', group='default')
        
        view1 = CDSView(source=self.source, filters=[gf])

        data_table1 = DataTable(source=self.source,
                                columns=columns,
                                editable=True,
                                width=600,
                                height=280,
                                auto_edit=False,
                                view=view1
                               )
        data_table2 = DataTable(source=self.foi_master_cds,
                                columns=columns2,
                                editable = True,
                                width=600,
                                height=280,
                                auto_edit=False)
        js_code = """
        var foi_data = cb_obj.data
        var data = source.data
        for (let i = 0; i < foi_data['name'].length; i++) {

            var foi_name = foi_data['name'][i]

            for (let j = 0; j < data['foi'].length; j++) {
                var foi = data['foi'][j]

                if (foi_name == foi) {
                    console.log("match, color changed");
                    data['color'][j] = foi_data['color'][i];
                    data['trans'][j] = foi_data['trans'][i];
                }
            }
        }

        source.change.emit()
        """
        
        js_code2 = """
        var data = source.data
        var name = data['name']
        var color = data['color']
        var trans = data['trans']
        var text = ti['value']
        
        data['name'].push(text)
        data['color'].push('firebrick')
        data['trans'].push(0.25)
        
        source.change.emit()
        """
        
        js_code3 = """
        var index = parseInt(cb_obj.indices)
        var data = source.data
        var name = data['name'][index]
        var text = ti['value']
        
        ti.value = name
        ti.change.emit()

        gf.group = name
        gf.change.emit()
        source2.change.emit()
        """
        
        
        callback = CustomJS(args=dict(source=self.source), code=js_code)
        
        self.foi_master_cds.js_on_change('patching', callback)
        
        text_input = TextInput(value="New FOI", title="New FOI Name")
        
        button = Button(label="Add FOI", button_type="success")
        callback2 = CustomJS(args=dict(source=self.foi_master_cds, ti=text_input), code=js_code2)
        button.js_on_click(callback2)
        
        callback3 = CustomJS(args=dict(source=self.foi_master_cds, source2=self.source, ti=text_select_foi, gf=gf), code=js_code3)
        self.foi_master_cds.selected.js_on_change('indices', callback3)
        
        return data_table1, data_table2, button, text_input, text_select_foi
    
    def foi_master_list(self):
        columns =  [
            TableColumn(field="name", title="Name"),
            TableColumn(field="color", title="Color")
            ]
        
        foi_master_list = DataTable(source=self.foi_master_cds,
                                   columns=columns,
                                   editable=True,
                                   width=400,
                                   height=280,
                                   auto_edit=False)
        button = Button(label="Add FOI", button_type="success")
        button.js_on_click(CustomJS(code="console.log('button: click!', this.toString())"))
    
    def foi_filter(self):
        menu=self.foi_mast_cds['name']
        dropdown = Dropdown(label="FOI", button_type="warning", menu=menu)
    
    def page(self):
        sh = self.spec_histogram()
        wf, tti = self.waterfall()
        swh = self.sweep_histogram()
        dt1, dt2, button, text_input, text_select_foi = self.data_table()
        grid = gridplot([[sh], [wf], [tti], [swh]], merge_tools=False)
        grid2 = gridplot([[text_select_foi], [dt1],  [text_input], [button], [dt2]])
        tab1_layout = layout(grid)
        tab2_layout = layout(grid2)
        tab1 = Panel(child=tab1_layout, title="Spectrum Data")
        tab2 = Panel(child=tab2_layout, title="FOI Tool")
        tabs = Tabs(tabs=[ tab1, tab2 ])
        output_file(f'{self.start_frq} - {self.stop_frq}.html', title='EME Analysis Tool', mode='inline')
        
        show(tabs)