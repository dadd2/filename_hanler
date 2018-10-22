from tkinter import *

class ButtonCanvas(Canvas):
    """предоставляет кнопочки увелчить/уменьшить для числовых полей"""
    def __init__(self, *args, w=20, h=20,
        arrow_oncolor='blue', letter_oncolor='#faa', offcolor='white',
        letters=[None, None], clicable_state=True, callback=None, **kw):
        """инициализация

        callback на самом деле обязательный параметр"""
        assert callback is not None
        super().__init__(*args, width=w, height=h, **kw)
        # self.place(w=w, h=h, **placekw)
        self.clicable_state = clicable_state
        self.colors = [offcolor, arrow_oncolor, letter_oncolor]
        self.letters = letters
        self.external_callback = callback

        self.create_rectangle([0, 0], [w, h/2], fill=self.colors[0], tag='up')
        self.create_rectangle([0, h/2], [w, h], fill=self.colors[0], tag='down')

        l=4
        k=2
        self.create_line([w/2-l, h/4+k], [w/2, h/4-k], [w/2+l, h/4+k], fill=self.colors[1], tag='up_arrow')
        self.create_line([w/2-l, h*3/4-k], [w/2, h*3/4+k], [w/2+l, h*3/4-k], fill=self.colors[1], tag='down_arrow')
        
        # print(self.letters)
        default_text = [self.letters[i][0] if self.letters[i] is not None else ' ' for i in [0, 1]]
        self.create_text([w/2, h/4], text=default_text[0], fill=self.colors[2], tag='up_letter')
        self.create_text([w/2, h*3/4], text=default_text[1], fill=self.colors[2], tag='down_letter')
        
        def get_callback(kind, direction):
            return lambda event: self.clickable_callback(kind, direction)
        for kind in ('up', 'down'):
            for direction in ('Press', 'Release'):
                self.tag_bind(kind, '<Button{}-1>'.format(direction), get_callback(kind, direction))
                self.tag_bind(kind+'_arrow', '<Button{}-1>'.format(direction), get_callback(kind, direction))

    def set_clickable_state(self, newstate):
        if self.clicable_state == newstate:
            return
        assert newstate in [0, 1]
        self.itemconfig('down_arrow', fill=['white', self.colors[1]][newstate])
        self.itemconfig('up_arrow', fill=['white', self.colors[1]][newstate])
        self.itemconfig('up_letter', fill=[self.colors[2], 'white'][newstate])
        self.itemconfig('down_letter', fill=[self.colors[2], 'white'][newstate])
        for key_ in ['up_', 'down_']:
            self.tag_raise(key_ + ['letter', 'arrow'][newstate])
            self.tag_lower(key_ + ['letter', 'arrow'][1-newstate])
        self.clicable_state = newstate
    
    def key_callback(self, event, direction):
        # raise Warning('test this function')
        directions = ('Press', 'Release')
        kinds = ('up', 'down')
        assert direction in directions
        di = directions.index(direction)

        if not self.clicable_state and isinstance(event.char, str) and len(event.char) == 1:
            for i, kind in enumerate(kinds):
                if event.char in self.letters[i]:
                    self.itemconfig(kind, fill=self.colors[::2][1-di])
                    self.itemconfig(kind + '_arrow', fill=self.colors[::2][di])
                    self.itemconfig(kind + '_letter', fill=self.colors[::1][di])
            if direction == 'down':
                return True
        return False
    
    def clickable_callback(self, kind, direction):
        if not self.clicable_state:
            return
        """управление внешним видом; при Press -- вызов external_callback

        kind could be 'up' or 'down'
        direction could be 'Press' or 'Release'"""
        directions = ('Press', 'Release')
        kinds = ('up', 'down')
        assert kind in kinds
        assert direction in directions

        di = directions.index(direction)
        self.itemconfig(kind, fill=self.colors[1-di])
        self.itemconfig(kind + '_arrow', fill=self.colors[di])
        if direction == 'Press':
            self.external_callback(kind, direction)
