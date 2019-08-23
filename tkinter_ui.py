import files_handler
from button_canvas import ButtonCanvas
# from getattrable_dict import OrderedDict as ListDict

from tkinter import *
from tkinter import messagebox
import time
import copy
import time
import os

# TODO 2019:
# - переписать с OrderedDict
# - добавить "паузу" после сна
# - изменить логику кнопок pause/unlock
# - добавить кнопки перемешения вверх/вниз в списке
# - разобраться с отображением времени
# - ДОЛБАНЫЕ ЦВЕТА
# - Ввести нормальную терминологию для "первая строкаа", "вторая строка", 
# - сделать документацию с i,j (или j,k_)
# - сделать представление зависимостей !!!!!!!


oldsize = [0]   # fixme это чо?
# ui elements:
# counter of bad files (an other statistics...)
# history
# namechange field

# todo:
# embed russification possibility
# сделать какое-нибудь мигание при обновлении данных
GRADS = [' '] + [chr(i) for i in range(9615, 9607, -1)]
HGRADS = [chr(i) for i in range(9608, 9600, -1)] + [' ']

HEX_ALPH = []
for i in '0123456789abcdef':
    for j in '0123456789abcdef':
        HEX_ALPH.append(i+j)

COOKING_GRADS = [[100, 100, 255], [255, 255, 255]]
TIMING_GRADS = [[255, 255, 255], [150, 255, 150]]


def gradline_old(x, k):
    if x > k:
        x = k
    blocks = GRADS[-1] * int(x)
    # print(blocks+'-')
    if x > int(x):
        blocks += GRADS[int(x % 1 * (len(GRADS)))]
    return blocks + ' ' * (k - len(blocks))
def gradline(x, k):
    p = int(x/k * 100)
    if p > 100:
        p = 100
    return '{:>4}%'.format(p)

def hexcolor(rgb):
    return '#' + ''.join(HEX_ALPH[int(i)] for i in rgb)


def gradient(a, b, x):
    if x < 0:
        x = 0
    elif x > 1:
        x = 1
    return [a_ * (1-x) + b_ * x for a_, b_ in zip(a, b)]
# print('-' + gradline(4,4) + '-')


class ListDict(list):
    '''велосипед для collections.OrderedDict
    TODO: переписать всё с OrderedDict'''
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
    """главный класс в проекте"""

    # var supply: 0
    def __init__(self, data_location):
        """первая стадия инициализации, до создания FileHandler (остальное -- в _init_2 при вызове mainloop)
        data_location один раз передаётся в self.fh; рефакторить при работе с конфигами

        Описание работы:
        - создаёт словари для хранения элементов GUI (в т. ч. тех, что введутся в _init_2)
        - создаёт элементы гуи, независимые от конкретного FileHandler
        
        TODO:
        - помеить разделы кода
        """
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
            # TODO: divide into "entrys-int" / "entrys-var" etc
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
        self.root.minsize(height=300, width=320)
        self.root.geometry('{w}x{h}'.format(h=300, w=320))
        self.root.resizable(True, True)
        self.root.title('files handler by dadd2')

        self.main_frame = Frame(self.root)
        r=3
        self.main_frame.place(x=r, y=r, relwidth=1, relheight=1, width=-2*r, height=-2*r)

        self.entrys_frame = Frame(self.main_frame)
        self.entrys_frame.place(relwidth=1, height=30)

        self.buttons_frame = Frame(self.main_frame)
        self.buttons_frame.place(y=30, relwidth=1, height=30)

        self.stat_frame = Frame(self.main_frame, bg='red')
        self.stat_frame.place(y=60, relwidth=1, height=40)

        self.lists_frame = Frame(self.main_frame)
        self.lists_frame.place(y=100, relwidth=1, height=-90, relheight=1)

        place_args = [   # TODO переназвать place_args понятнее
            {'height': 60},
            {'height': 60, 'y': 60},
            {'y': 120, 'relheight': 1, 'height': -130},
        ]
        for i, place_arg in enumerate(place_args):
            la = {'relwidth': 1, 'width': -15}
            sa = {'anchor': 'ne', 'relx': 1}
            la.update(place_arg)
            sa.update(place_arg)

            self.lists_items['lists'].append(Listbox(self.lists_frame, font='Menlo 9'))
            self.lists_items['scrolls'].append(Scrollbar(
                self.lists_frame,
                orient=VERTICAL,
                command=self.lists_items ['lists'][-1].yview
            ))
            self.lists_items['lists'][-1]['yscrollcommand'] = self.lists_items['scrolls'][-1].set
            self.lists_items['lists'][-1].place(la)
            self.lists_items['scrolls'][-1].place(sa)
        if False:
            for i, line in enumerate(['todo:', '- messages', '- color indicate unfocus', '- work with pause condition',
                                      '- make soft insertion', '-use backgrounds']):
                self.lists_items['lists'][0].insert(END, line)
            self.lists_items['lists'][0].itemconfig(i, bg='yellow', selectbackground='red')
            # print(self.lists_items['lists'][0].itemconfig(i))
        
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

    # var supply: 0
    def mainloop(self):
        """Планирует вызов к self._init_2 и вызывает self.root.mainloop
        TODO: вспомнить, зачем вызов _init_2 завёрнут в after"""
        self.root.after(200, self._init_2)
        self.root.mainloop()

    # var supply: +/-
    def _init_2(self):
        """часть инициализации, которая объявляет FileHandler и использует данные из неё; здесь достраивается интерфейс

        План работы:
        - инициализирует self.fh -- бэкендовый объект из files_handler.py
        - в соответствии с прочитанными настройками создаёт строку с полями имени файла
        - биндит keypress/keyrelease на self.keys_callback
        - биндит focusin/focusout на self.focus_change_callback
        - вызывает self.fh.correcf; self.fh.ui_setup
        - вызывает self.update"""
        self.fh = files_handler.FilesHandler(self.data_location, self)
        self.root.title('{} -> {}'.format(
            os.path.split(self.fh.settings['source-folder'])[1],
            os.path.split(self.fh.settings['destination-folder'])[1]
        ))

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
                elif elem[0] == 'var':
                    # fixme: rework GUI to support any class of modifiers
                    def get_callback(i):
                        return lambda kind, direction, source: self.arrows_callback(i, kind, source)
                    self.entrys_elems_collection.append(Entry(
                        self.entrys_frame,
                        width=max(map(len, elem[1])),
                        state='normal',
                        disabledbackground=self.pal['entrys'][2],
                        disabledforeground='black'
                    ))
                    self.formatters_content.append([len(self.entrys_elems_collection)-1, i])

                    self.entrys_elems_collection.append(ButtonCanvas(
                        self.entrys_frame,
                        w=15, h=30,
                        letters=elem[4],
                        callback=get_callback(len(self.entrys_elems_collection)-1)))

                elif elem[0] == 'ext':
                    self.entrys_elems_collection.append(Label(self.entrys_frame, text='.[ext]'))
                else:
                    raise NotImplementedError()
        for entry_elem in self.entrys_elems_collection:
            entry_elem.pack(side=LEFT)
        self.root.bind_all('<KeyPress>', lambda event: self.keys_callback(event, 'Press'))
        self.root.bind_all('<KeyRelease>', lambda event: self.keys_callback(event, 'Release'))
        self.root.bind('<FocusIn>', lambda event: self.focus_change_callback(1))
        self.root.bind('<FocusOut>', lambda event: self.focus_change_callback(0))
        self.fh.correct()
        print('corrected')
        self.fh.ui_setup()
        self.init_complete = False
        self.update()

    # var supply: 0
    def focus_change_callback(self, newstate):
        """изменяет цвет рамки для обозначения, активно ли окно"""
        assert newstate in (0, 1)
        # print('fcc', newstate, time.time())
        self.root['bg'] = ['white', 'blue'][newstate]

    # var supply: 0
    def button_elem_callback(self, btname):
        '''обработка вызова кнопок correct, reset, lock/unlock, pause/resume
        TODO:
        - разобраться с apply, точнее implement его'''
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

    # var supply: 0
    def arrows_callback(self, i_, kind, source):
        """вызывается из ButtonCanvas (то есть из части окна, где строка с modifiers)"""
        # print(i_, self.formatters_content)
        i = [i for i, (j, k) in enumerate(self.formatters_content) if j == i_][0]
        # print(i)
        self.fh.modifier_increm(i, [1, -1][('up', 'down').index(kind)], save_others=source=='click')

    # var supply: 0
    def keys_callback(self, event, direction):
        """вызывается из self.root.bind_all('<KeyPress>', ...) и т. п.
        передаёт этот вызов на ButtonCanvas'ы"""
        for j, k in self.formatters_content:
            self.entrys_elems_collection[j+1].key_callback(event, direction)

    # var supply: 0
    def ask_alter(self, msg, default=1):
        """обёртка для messagebox.askyesno
        
        todo: ПРОТЕСТИРОВАТЬ НАЖАТИЕ НА КРЕСТИК И None
        fixme: is called also when src directory should be empty
        """
        return messagebox.askyesno(title='question', message=msg + '?')

    # var supply: 0
    def lock_switch(self, state='normal'):
        """переключает состояния и тексты кнопок из второй строки в соответствии с требованием

        TODO:
        - добавить связь с флагами состояние self
        - понять, зачем нужна кнопка "apply"
        """
        states = ('normal', 'disabled')
        i = states.index(state)
        for j, k in self.formatters_content:
            self.entrys_elems_collection[j]['state'] = state
            self.entrys_elems_collection[j+1].set_clickable_state(1-i)
        self.button_elems_coolection['correctbt'].config(state=state)
        self.button_elems_coolection['applybt'].config(state=state)
        self.button_elems_coolection['lockbt'].config(text=('lock', 'unlock')[i])

    # var supply: 0
    def pause_switch(self, direction='pause'):
        """переключает состояния и тексты кнопок из второй строки в соответствии с требованием

        TODO: добавить связь с флагами состояния self"""
        print('pause switch', direction, time.strftime('%T'))
        directions = ('pause', 'resume')
        states = ('normal', 'disabled')
        i = directions.index(direction)

        self.lock_switch(states[i])
        self.button_elems_coolection['pausebt'].config(text=directions[1-i])
        self.button_elems_coolection['lockbt'].config(state=states[i])
        self.button_elems_coolection['applybt'].config(state=states[i])

    # var supply: 0
    def get_modifiers(self):
        """вызывается из FileHandler, возвращает массив содержимого entrys"""
        return [self.entrys_elems_collection[j].get() for j, i in self.formatters_content]

    # var supply: 0
    def set_modifiers(self, modifiers):
        """вызывается из FileHandler; обновляет modifiers в GUI

        План обработки одного modifier:
        - сравниваем со старой версией, если есть разница:
            - пляшем с entry.state (ибо при disabled нельзя изменять содержимое)
            - вставляем свой текст"""
        assert len(modifiers) == len(self.formatters_content)
        for new, (j, i), old in zip(modifiers, self.formatters_content, self.get_modifiers()):
            # print('set_modifiers', new, i, j, old)
            if old != new:
                # print('set_modifiers: enter if')
                oldstate = self.entrys_elems_collection[j]['state']
                if oldstate != 'normal':
                    self.entrys_elems_collection[j]['state'] = 'normal'
                self.entrys_elems_collection[j].delete(0, END)
                self.entrys_elems_collection[j].insert(END, new)
                if oldstate != 'normal':
                    self.entrys_elems_collection[j]['state'] = oldstate
            # TODO add soft replace (replace changed rows only)

    # var supply: 0
    def set_incorrect(self, correct_flags):
        """paint incorrect modifiers in pink (both enabled and disabled background)"""
        for flag, (j, k) in zip(correct_flags, self.formatters_content):
            # disabledbackground
            self.entrys_elems_collection[j]['bg'] = self.pal['entrys'][1-flag]
            self.entrys_elems_collection[j]['disabledbackground'] = self.pal['entrys'][1+flag]

    # var supply 0
    def update(self):
        """вызывается с 10 FPS и держит всё в рабочем состоянии
        План работы:
        - вызываем аналогичную функцию у FilesHandler
        - обновляем lists (появились ли новые файлы, изменился ли статус, etc)
        - обновляем статисику
        - записываем себя в очередь через 100 ms

        TODO:
        - добиться того, чтобы здесь никогда не возникала ошибка
        - разобраться с умной задержкой времени
        """
        t_gui = time.time()
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
            else:
                k = 2
                for j, finfo in enumerate(new):
                    if j >= len(old) or finfo != old[j] or finfo['stage'] == 1:
                        stg_size = gradline(finfo['size'] / self.fh.settings['size-cooked'] * k, k)
                        if finfo['stage'] == 0:
                            stg_time = gradline(0, k)
                            bg_color = hexcolor(gradient(*COOKING_GRADS, finfo['size'] / self.fh.settings['size-cooked']))
                        elif finfo['stage'] == 1:
                            stg_time = gradline((t - finfo['mtime']) / self.fh.settings['cooking-time'] * k, k)
                            bg_color = hexcolor(gradient(*TIMING_GRADS, (t - finfo['mtime']) / self.fh.settings['cooking-time']))
                        else:
                            stg_time = gradline(k, k)
                            bg_color = hexcolor(gradient(*TIMING_GRADS, 1))
                        if j < len(old):
                            self.lists_items['lists'][i].delete(j)
                        self.lists_items['lists'][i].insert(END, '{stage}{stg_size}|{stg_time}| {fname}'.format(**finfo, **locals()))
                        self.lists_items['lists'][i].itemconfig(j, bg=bg_color, selectbackground=bg_color,
                                                                selectforeground='red')
                if len(new) < len(old):
                    self.lists_items['lists'][i].delete(len(new), END)

            # elif i == 0 and 1 in (finfo['stage'] for finfo in new):
                # pass
                # print(key, old, new, sep='\n', end='\n\n' + '-'*30 + '\n')
            self.dumps[key] = copy.deepcopy(new)
        # ------------ update statistics:
        grads2 = GRADS[1:] + GRADS[1:][::-1]
        self.stat_elems_collection['stats']['last_upd']['text'] = time.strftime('%T') + ' ' + grads2[int(time.time() % 1 * (len(grads2)))]
        newtime = time.time()
        self.stat_elems_collection['stats']['fps']['text'] = str(round(1 / (newtime - self.statistics['lasttime']),
                                                                       1)).zfill(4)
        self.statistics['lasttime'] = newtime
        # ------------ support loop
        self.root.update()
        if self.is_working:
            dt = max(70, 100 - int((time.time()-t_gui)*1000))
            # print(dt)
            self.root.after(dt, self.update)

if __name__ == '__main__':
	flag = 0
	try:
	    tfh = TkinterFilesHandler('asdf')
	    tfh.mainloop()
	    flag = 1
	finally:
		if not flag:
			input('press enter to exit')