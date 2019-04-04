import files_handler
from button_canvas import ButtonCanvas
# from getattrable_dict import OrderedDict as ListDict

from tkinter import *
from tkinter import messagebox
import time
import copy
import time

# TODO 2019:
# - переписать с OrderedDict
# - добавить "паузу" после сна
# - изменить логику кнопок pause/unlock
# - добавить кнопки перемешения вверх/вниз в списке
# - разобраться с отображением времени
# - ДОЛБАНЫЕ ЦВЕТА
# - 
oldsize = [0]
# ui elements:
# counter of bad files (an other statistics...)
# history
# namechange field

# todo:
# embed russification possibility
# сделать какое-нибудь мигание при обновлении данных
GRADS = [' '] + [chr(i) for i in range(9615, 9607, -1)]
HGRADS = [chr(i) for i in range(9608, 9600, -1)] + [' ']

def gradline(x, k):
    blocks = GRADS[-1] * int(x)
    # print(blocks+'-')
    if x > int(x):
        blocks += GRADS[int(x % 1 * (len(GRADS)))]
    return blocks + ' ' * (k - len(blocks))
# print('-' + gradline(4,4) + '-')

class ListDict(list):
    def __init__(self):
        super().__init__()
        self.__keys = {}
    
    def append(self, elem, key=None):
        super().append(elem)
        if key is not None:
            assert isinstance(key, str)
            # print('key append', key, len(self)-1, self.__keys, self)
            self.__keys[key] = len(self) - 1
    
    def __getitem__(self, key):
        if isinstance(key, int):
            return super().__getitem__(key)
        elif isinstance(key, str):
            return super().__getitem__(self.__keys[key])
        else:
            raise TypeError('key should be int or str')
    
    def get_withkeys(self):
        return [self[i] for k, i in sorted(self.__keys.items(), key=lambda pair: pair[1])]


class TkinterFilesHandler:
    """главный класс, ради которого всё и происходит"""
    def __init__(self, data_location):
        """первая стадия инициализации, до создания FileHandler (остальное -- при вызове mainloop)"""
        self.is_working = True
        self.init_complete = False  # unuseful flag; should be removed
        self.data_location = data_location

        self.ui_config = {
            "lists_patterns": []
        }
        self.entrys_elems_collection = []
        self.formatters_content = []
        self.lists_items = {'lists': [], 'scrolls': []}
        self.button_elems_coolection = {}
        self.stat_elems_collection = {'frames': [], 'stats': ListDict()}
        self.statistics = {
            'lasttime': time.time()
        }

        self.pal = {
            "entrys": ['white', 'pink', '#9f9']
        }
        self.dumps = {
            'files_history': [],
            'files_cooking': [],
            'files_ready': [],
            'last_update_time': {'cooking': 0, 'ready': 0, 'history': 0},
            'modifiers': []
        }
        self.root = Tk()

        self.root.geometry('{w}x{h}+{x}+{y}'.format(w=300, h=480, x=10, y=10))
        self.root.minsize(height=300, width=400)
        self.root.resizable(True, True)
        self.root.title('files handler by dadd2')

        self.main_frame = Frame(self.root)
        r=10
        self.main_frame.place(x=r, y=r, relwidth=1, relheight=1, width=-2*r, height=-2*r)

        self.entrys_frame = Frame(self.main_frame)
        self.entrys_frame.place(relwidth=1, height=30)

        self.buttons_frame = Frame(self.main_frame)
        self.buttons_frame.place(y=30, relwidth=1, height=30)

        self.stat_frame = Frame(self.main_frame, bg='red')
        self.stat_frame.place(y=60, relwidth=1, height=40)

        self.lists_frame = Frame(self.main_frame)
        self.lists_frame.place(y=100, relwidth=1, height=-90, relheight=1)

        place_args = [
            {'relheight': 0.4},
            {'rely': .4, 'height': 90},
            {'rely': .4, 'y': 90, 'relheight': .6, 'height': -90},
        ]
        for i, place_arg in enumerate(place_args):
            la = {'relwidth': 1, 'width': -30}
            sa = {'relx': 1, 'x': -30, 'width': 30}
            la.update(place_arg)
            sa.update(place_arg)

            self.lists_items['lists'].append(Listbox(self.lists_frame, font='Menlo 11'))
            self.lists_items['scrolls'].append(Scrollbar(
                self.lists_frame,
                orient=VERTICAL,
                command=self.lists_items ['lists'][-1].yview
            ))
            self.lists_items['lists'][-1]['yscrollcommand'] = self.lists_items['scrolls'][-1].set
            self.lists_items['lists'][-1].place(la)
            self.lists_items['scrolls'][-1].place(sa)
        for i, line in enumerate(['todo:', '- messages', '- color indicate unfocus', '- work with pause condition',
                                  '- make soft insertion', '-use backgrounds']):
            self.lists_items['lists'][0].insert(END, line)
        self.lists_items['lists'][0].itemconfig(i, bg='yellow', selectbackground='red')
        
        def get_command(text):
            return lambda: self.button_elem_callback(text + 'bt')
        for i, text in enumerate(['correct', 'reset', 'pause', 'lock', 'apply']):
            self.button_elems_coolection[text + 'bt'] = (Button(self.buttons_frame, text=text, command = get_command(text)))
            self.button_elems_coolection[text + 'bt'].pack(side=LEFT)
    
        self.stat_elems_collection['frames'] = [Frame(self.stat_frame), Frame(self.stat_frame)]
        [frame.place(relwidth=1, relheight=.5, rely=i/2) for i, frame in enumerate(self.stat_elems_collection['frames'])]
        tagss = [['last_upd', 'fps'], ['done', 'ready']]
        for i, tags in enumerate(tagss):
            for tag in tags:
                self.stat_elems_collection['stats'].append(Label(
                        self.stat_elems_collection['frames'][i],
                        fg='gray',
                        text=tag+':'
                ))
                self.stat_elems_collection['stats'].append(
                    Label(
                        self.stat_elems_collection['frames'][i],
                        fg='blue',
                        text=''
                    ),
                    key=tag
                )
        for elem in self.stat_elems_collection['stats']:
            elem.pack(side=LEFT)
    
    def mainloop(self):
        """эта функция кроме root.mainloop вызывает ещё self._init_2"""
        self.root.after(200, self._init_2)
        self.root.mainloop()

    def _init_2(self):
        """часть инициализации, которая объявляет FileHandler и использует данные из неё; здесь достраивается интерфейс"""
        self.fh = files_handler.FilesHandler(self.data_location, self)

        for i, elem in enumerate(self.fh.settings['name-pattern']):
            if isinstance(elem, str):
                self.entrys_elems_collection.append(Label(self.entrys_frame, text=elem))
            elif isinstance(elem, list):
                if elem[0] == 'int':
                    def get_callback(i):
                        return lambda kind, direction, source: self.arrows_callback(i, kind, source)
                    self.entrys_elems_collection.append(Entry(
                        self.entrys_frame,
                        width=elem[1],
                        state='normal',
                        disabledbackground=self.pal['entrys'][2],
                        disabledforeground='black'
                    ))
                    self.formatters_content.append([len(self.entrys_elems_collection)-1, i])

                    self.entrys_elems_collection.append(ButtonCanvas(
                        self.entrys_frame,
                        w=15, h=30,
                        letters=elem[5],
                        callback=get_callback(len(self.entrys_elems_collection)-1)))
                elif elem[0] == 'ext':
                    self.entrys_elems_collection.append(Label(self.entrys_frame, text='.[ext]'))
                else:
                    raise NotImplementedError()
        for entry_elem in self.entrys_elems_collection:
            entry_elem.pack(side=LEFT)
        self.root.bind_all('<KeyPress>', lambda event: self.keys_callback(event, 'Press'))
        self.root.bind_all('<KeyRelease>', lambda event: self.keys_callback(event, 'Release'))
        self.fh.correct()
        print('corrected')
        self.fh.ui_setup()
        self.init_complete = False
        self.update()

    def button_elem_callback(self, btname):
        '''обработка вызова кнопок correct, reset, lock/unlock, pause/resume'''
        text = self.button_elems_coolection[btname]['text']
        print('button_elem_callback', btname, text)
        if btname == 'lockbt':
            self.lock_switch(state=['normal', 'disabled'][1-('lock', 'unlock').index(text)])
        elif btname == 'pausebt':
            [self.fh.pause, self.fh.resume][('pause', 'resume').index(text)]()
        elif btname == 'correctbt':
            self.fh.correct()
        elif btname == 'resetbt':
            self.fh.reset()
    
    def arrows_callback(self, i_, kind, source):
        """is called from lambda which defined in _init_2"""
        # print(i_, self.formatters_content)
        i = [i for i, (j, k) in enumerate(self.formatters_content) if j == i_][0]
        # print(i)
        self.fh.modifier_increm(i, [1, -1][('up', 'down').index(kind)], save_others=source=='click')
    
    def keys_callback(self, event, direction):
        for j, k in self.formatters_content:
            self.entrys_elems_collection[j+1].key_callback(event, direction)
        
    def ask_alter(self, msg, default=1):
        """обёртка для messagebox """
        # todo: ПРОТЕСТИРОВАТЬ НАЖАТИЕ НА КРЕСТИК И None
        # fixme: is called also when src directory should be empty
        return messagebox.askyesno(title='question', message=msg + '?')

    def lock_switch(self, state='normal'):
        states = ('normal', 'disabled')
        i = states.index(state)
        for j, k in self.formatters_content:
            self.entrys_elems_collection[j]['state'] = state
            self.entrys_elems_collection[j+1].set_clickable_state(1-i)
        self.button_elems_coolection['correctbt'].config(state=state)
        self.button_elems_coolection['applybt'].config(state=state)
        self.button_elems_coolection['lockbt'].config(text=('lock', 'unlock')[i])

    def pause_switch(self, direction='pause'):
        print('pause switch', direction, time.strftime('%T'))
        directions = ('pause', 'resume')
        states = ('normal', 'disabled')
        i = directions.index(direction)

        self.lock_switch(states[i])
        self.button_elems_coolection['pausebt'].config(text=directions[1-i])
        self.button_elems_coolection['lockbt'].config(state=states[i])
        self.button_elems_coolection['applybt'].config(state=states[i])

    def get_modifiers(self):
        """вызывается из FileHandler, возвращает массив из entrys"""
        return [self.entrys_elems_collection[j].get() for j, i in self.formatters_content]
        # raise NotImplementedError()
    
    def set_modifiers(self, modifiers):
        assert len(modifiers) == len(self.formatters_content)
        for new, (j, i), old in zip(modifiers, self.formatters_content, self.get_modifiers()):
            if old != new:
                oldstate = self.entrys_elems_collection[j]['state']
                if oldstate != 'normal':
                    self.entrys_elems_collection[j]['state'] = 'normal'
                self.entrys_elems_collection[j].delete(0, END)
                self.entrys_elems_collection[j].insert(END, new)
                if oldstate != 'normal':
                    self.entrys_elems_collection[j]['state'] = oldstate
            # TODO add soft replace (replace changed rows only)
    
    def set_incorrect(self, correct_flags):
        """paint incorrect modifiers in pink"""
        for flag, (j, k) in zip(correct_flags, self.formatters_content):
            # disabledbackground
            self.entrys_elems_collection[j]['bg'] = self.pal['entrys'][1-flag]
            self.entrys_elems_collection[j]['disabledbackground'] = self.pal['entrys'][1+flag]

    def update(self):
        self.fh.mainloop_cycle()
        # update lists
        # update entrys content
        # update statistics

        # print(self.fh.validate(self.get_modifiers()))
        # if self.fh.paused:
        #     for (j, i), flag in zip(self.formatters_content, self.fh.validate(self.get_modifiers())):
        #         self.entrys_elems_collection[j]['bg'] = self.pal['entrys'][not flag]
        # ------------ update lists:
        t = time.time()
        for i, key in enumerate(('files_cooking', 'files_ready', 'files_history')):
            old, new = self.dumps[key], getattr(self.fh, key)
            if i == 2:
                if new != old:
                    for finfo in new[len(old):]:
                        self.lists_items['lists'][i].insert(0, '{fname-new} / {fname}'.format(**finfo))

            elif new != old:
                self.lists_items['lists'][i].delete(0, END)
                for finfo in new:
                    k = 5
                    if finfo['stage'] == 0:
                        stg = gradline(finfo['size'] / self.fh.settings['size-cooked'] * k, k)
                    elif finfo['stage'] == 1:
                        stg = gradline((t - finfo['mtime']) / self.fh.settings['cooking-time'] * k, k)
                    else:
                        stg = gradline(k, k)
                    self.lists_items['lists'][i].insert(END, '{stage} [{stg}] {fname}'.format(stg=stg, **finfo))
            elif i == 0 and 1 in (finfo['stage'] for finfo in new):
                pass
                # print(key, old, new, sep='\n', end='\n\n' + '-'*30 + '\n')
            self.dumps[key] = copy.deepcopy(new)
        # ------------ update statistics:
        grads2 = GRADS[1:] + GRADS[1:][::-1]
        self.stat_elems_collection['stats']['last_upd']['text'] = time.strftime('%T') + ' ' + grads2[int(time.time() % 1 * (len(grads2)))]
        newtime = time.time()
        self.stat_elems_collection['stats']['fps']['text'] = round(1 / (newtime - self.statistics['lasttime']), 1)
        self.statistics['lasttime'] = newtime
        # ------------ support loop
        self.root.update()
        if self.is_working:
            self.root.after(100, self.update)

if __name__ == '__main__':
    tfh = TkinterFilesHandler('asdf')
    tfh.mainloop()
