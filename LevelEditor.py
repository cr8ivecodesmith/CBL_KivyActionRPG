import kivy
from kivy.uix.widget import Widget
from kivy.properties import NumericProperty, BooleanProperty, ListProperty, StringProperty, ObjectProperty
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.atlas import Atlas
from kivy.app import App
from kivy.core.window import Window
from kivy.clock import Clock
from kivy.factory import Factory
import time
import os
from BaseObjects import WorldObject, Subtile, Tile, Screen, CBLPopup
from DatabaseReader import DatabaseReader



class ScreenEditor(FloatLayout):

    button_width = NumericProperty(80)
    button_height = NumericProperty(80)
    spacing = NumericProperty(10)
    level = ObjectProperty(None)

    def __init__(self,dbr,maplabel,screenid,**kwargs):
        self.tileset = dbr.tile_dict.values()
        print "tileset:",self.tileset
        self.init_tile_list = dbr.get_screen(maplabel,screenid)
        self.current_tile_type = self.tileset[0]

        # will be removed
        object_atlas='ArtAssets/WorldObjects/WorldObjects-SeaGrass_Forest-Set1_128.atlas'
        self.objectset = self.get_world_objects(object_atlas)
        

        self.commands = {
            "Save": self.save_screen,
            "Close": self.close_screen,
        }

        super(ScreenEditor,self).__init__(**kwargs)
        Clock.schedule_once(self.setup_window)
        

    def setup_window(self,dt):
        # draw buttons for the commands, the tileset, and the object set
        self.draw_buttons(self.commands.keys(),self.tileset,self.objectset)

        self.screen = Screen(
            self.tileset,
            self.init_tile_list,
            parent = self,
            x = self.x + self.button_width + 2*self.spacing,
            y = self.y + self.spacing,
            size = (self.width - self.button_width - 2*self.spacing, self.height - 2*self.spacing),
            size_hint = (None,None),
            spacing = 0,
            padding = 0,
            )


        self.add_widget(self.screen)


    def get_world_objects(self,atlas):
        '''Reads all world objects from supplied atlas. Returns a list of WorldObjects'''
        # split all keys into tile groups (i.e., make xx-1 xx-2 xx-3 and xx-4 into the same object)
        objects = []
        for key in Atlas(atlas).textures.keys():
            keysplit = key.rpartition('-')
            #try to cast the last section of the name after - as an int. if this works it's an animated frame
            try:
                fnum = int(keysplit[-1])
                # now add the section of the name prior to the '-' as a key to objects if it's not there already, otherwise increment frames by 1.

                if keysplit[0] not in [x.name for x in objects]:
                    objects.append(WorldObject(atlas,keysplit[0],1))
                else:
                    objects[[x.name for x in objects].index(keysplit[0])].frames += 1

            except ValueError:
                objects.append(WorldObject(atlas,key,1))

        return objects

    def draw_buttons(self,text_buttons,buttons,objects):

        bl = BoxLayout(
            orientation = 'vertical',
            spacing = self.spacing,
            size_hint_y = None, 
            height = len(buttons+objects+text_buttons)*(self.spacing + self.button_height) + self.spacing,
            )

        # these don't really need to be separate at all
        for t in text_buttons:
            b = Button(text=str(t), id = str(t), size_hint_y = None, height = self.button_height)
            b.bind(on_release = self.button_callback)
            bl.add_widget(b)

        for t in buttons:
            b = Button(text="", id = t.material_name, background_normal = t.icon_str, background_down = t.icon_str, size_hint_y = None, height = self.button_height)
            b.bind(on_release = self.button_callback)
            bl.add_widget(b)

        for o in objects:
            b = Button(text="", id = o.name, background_down = o.icon_str, background_normal = o.icon_str, size_hint_y = None, height = self.button_height)
            b.bind(on_release = self.button_callback)
            bl.add_widget(b)

        sv = ScrollView(size_hint = (None, None), width=self.button_width, height = self.height, x = self.x + self.spacing,
            y = self.y + self.spacing)
        sv.add_widget(bl)
        self.add_widget(sv)

    def button_callback(self, instance):
        if instance.id in self.commands.keys():
            self.commands[instance.id]()
        elif instance.id in [x.material_name for x in self.tileset]:
            self.current_tile_type = self.tileset[[x.material_name for x in self.tileset].index(instance.id)]
        elif instance.id in [x.name for x in self.objectset]:
            self.current_tile_type = self.objectset[[x.name for x in self.objectset].index(instance.id)]

    def save_screen(self):
        print "just saved the screen"

    def close_screen(self):
        print "closed screen"
        



class MapEditorWidget(FloatLayout):

    def __init__(self,**kwargs):
        super(MapEditorWidget,self).__init__(**kwargs)
        
        # open up worlddb.sqlite, for now
        self.dbr = DatabaseReader(os.path.join(os.path.dirname(__file__),'worlddb.sqlite'))
        
        pu = CBLPopup(self.menu_callback,title='Tales of Isan: Level Editor', buttons=['New Map','Load Map','Close'], size_hint=(.4,.4))
        pu.open()

    def menu_callback(self,instance):
        print instance.text
        if instance.text == 'New Map':
            self.create_map('000')
        elif instance.text == 'Load Map':
            self.load_map()

    def create_map(self,maplabel):
        self.rows = 6
        self.cols = 9

        # this should be somewhere else
        self.dbr.add_tileset([Subtile('atlas://ArtAssets/TileSets/Tileset-SeaGrass_Forest_128/','Grass',None,1),
            Subtile('atlas://ArtAssets/TileSets/Tileset-SeaGrass_Forest_128/','Sand',None,1),
            Subtile('atlas://ArtAssets/TileSets/Tileset-SeaGrass_Forest_128/','Water',None,4),
            Subtile('atlas://ArtAssets/TileSets/Tileset-SeaGrass_Forest_128/','Dirt',None,1)])

        # for debugging, ignore if map already exists
        self.dbr.add_map(maplabel,rows=self.rows,cols=self.cols)

        # get all tiles used in the database
        tileset = self.dbr.tile_dict

        # now make a screen filled with the second item in the tileset
        first_tile_id = tileset.keys()[1]
        tiles = [[first_tile_id] for i in xrange(int(self.rows)) for j in xrange(int(self.cols))]
        screenid = self.dbr.add_screen(tiles,None,maplabel,None,None)
        
        # screen_editor = ScreenEditor(self.dbr,maplabel,screenid)
        # self.add_widget(screen_editor)

    def load_map(self,maplabel):
        pass


class LevelEditorApp(App):
    def build(self):
        main = MapEditorWidget()
        return main


if __name__ == '__main__':
    LevelEditorApp().run()
