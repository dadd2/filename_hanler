import re
import os
import time
import itertools as it
import pprint
import copy
import json

# TODO 2019:
# - перенести chunksize (при копировании) в json настроек
# - оценить состояние проекта; перенести все TODO в отдельный файл
# - сделать норм описание, например:                 !!!!!!!!!!!!!!!АААААА
#   - краткая формулировка;
#   - комментарии к входным данным;
#   - суть процесса (стадии, заметки к формулам и прочая);
#   - описание вывода, побочников и прочая;
#   - TODO-раздел;
# - сделать string-паттерны (свой текст; выбор из списка), но это потом
# - реализовать уже наконец чтение настроек откуда нада
#   - рабочие настройки, в буфере приложения
#   - экспорт/импорт в файл
# - переделать описание инта по шаблону: минимальное значение, максимальное значение
# - написать логирование; вывести опцию в settings
# - нарисовать в какой-нить проге модель взаимодействия всей этой гажи
# - развернуть стрелки от VC к M

# TODO:
# - error tracking
# - whatto do if filename is in use (возможно, имелось в виду destination filename)
# + stop the process if >1 file cooked (optional) or old files
# + make independence of what time is using on host computer
# - settings editing scheme (how user do it?)
# - if it's future time on disk?
# - 

# far future TODO:
# add tracking file history
# add image show
# add whatto do in case of:
# - unexpected file removal before processing
# - "not permitted" and others operations

# name pattern contents:

# length of field (if 0 -- don't reset)
# write leading zeros
# increment on every file (optional, could be only one such thing)

# name-pattern element:
# first param: class
# for int:
# [class, ndigits, default, write_leading_zeros, is_autoincrement, hotkeys]
# for str:
# [class, entry_width, default]
# for var:
# [class, variants, default, needs_reset, hotkeys]
# for ext:
# [class]

COSTYL_PATH=True
base_settings = {
    "source-folder": "/Users/dadd2/Documents/unreal_life/newEOS_base/srcb",
    "destination-folder": "/Users/dadd2/Documents/unreal_life/newEOS_base/dest",
    "history-file": None,  # "history.txt",
    "file-excluding-patterns": [r"^\.DS_Store$", r'\.tiff-'],
    "name-pattern": [
        '1-1-',
        ['int', 4, 1, False, False, ['qй', 'aф']],
        '-',
        ['int', 2, 1, False, True, ['wц', 'sы']],
        ['var', ['', 'а', 'б', 'в', 'г', 'д', 'е', 'ж', 'з', 'и', 'к', 'л', 'м', 'н', 'о', 'п', 'р', 'с', 'т', 'у',
                 'ф', 'х', 'ц', 'ч', 'ш', 'ы', 'э', 'ю', 'я'], 0, True, ['eу', 'dв']],
        ['var', ['', ' об', ' доп'], 0, True, ['rк', 'fа']],
        ['ext']
    ],
    "size-cooked": 50,
    "cooking-time": 2.5,
    "reloading-delay": 10,
    "seconds-for-overload": 5,
    "update-peiod-ms": 200
}


def dict2list(d):
    """переделывает словарь в список из [key] + value"""
    return list([k] + list(v) for k, v in d.items())


def cut_not_digits(s):
    """вырезает все не-цифры из строки"""
    return ''.join(c for c in s if c in '01234567890')


def fmove(src, dst, chunk=1024*512):
    """двигает файл (пока без обработки ошибок)"""
    assert isinstance(chunk, int) and chunk > 0
    os.makedirs(os.path.split(dst)[0], exist_ok=True)
    with open(src, 'br') as srcfile:
        with open(dst, 'bw') as dstfile:
            while True:
                r = srcfile.read(chunk)
                if r == b'':
                    break
                dstfile.write(r)
                # print('srcfile chunk')
    os.remove(src)


def soft_open(path, mode='r', ok_callback=lambda f:f.read(), err_callback=lambda e: ''):
    """открывает файл; при успехе -- один колбэк, при ошибке -- второй"""
    try:
        with open(path, mode) as file:
            return ok_callback(file)
    except Exception as e:
        return err_callback(e)


class ConsoleUI:
    """костыль для пробных запусков"""
    def __init__(self):
        pass
    
    def ask_alter(self, msg, default=1):
        if default == 1:
            chars = 'Yn'
            answs = 'nN'
        elif default == 0:
            chars = 'yN'
            answs = 'yY'
        else:
            raise ValueError('default param should be 1 or 0')

        answ = input('{} [{}/{}]'.format(msg, *chars))
        return (answ in answs) ^ default
   
    def pause(self):
        pass
    
    def resume(self):
        pass
    
    def get_modifiers(self):
        raise NotImplementedError()
    
    def set_modifiers(self, modifiers):
        raise NotImplementedError()

    def set_incorrect(self, correct_flags):
        print('correct_flags:', correct_flags)


class FilesHandler:
    """главный класс, который лежит под капотом у tkinterui, содержит всю логику отслеживания и управления файлами"""

    # var supply: 0
    def __init__(self, settings_location, ui):
        """ну, понятно

        эта ф-ция успевает 1 раз обратиться к ui.ask_alter"""
        self.settings_location = settings_location
        self.settings = soft_open(
            settings_location,
            'r',
            lambda f: json.load(f),
            lambda e: (print('soft_open error'), base_settings)[1]
        )
        self.ui = ui

        self.files_history = []
        self.files_cooking = []
        self.files_ready = []

        self.paused = False
        self.oldfiles = False
        self.last_update_time = {'cooking': 0, 'ready': 0, 'history': 0}
        finfos = list(self.get_directory_content(is_first=True))
        if finfos:
            if ui.ask_alter('there are some files in the directory. should we clean the directory before work'):
                for finfo in finfos:
                    os.remove(os.path.join(self.settings['source-folder'], finfo['fname']))
            else:
                self.oldfiles = True

    # var supply: 0
    def get_directory_content(self, is_first):
        """возвращает массив из fileinfos
        (каждое fileinfo -- словарь из ino, size, stage, fname, addtime, ...)

        есть обработка отстающего времени в src-папке, но нет опережающего
        нет никакой обработки перебоев связи. ВООБЩЕ НИКАКОЙ
        TODO писать тесты на всякие шутки со временем"""
        for fname in os.listdir(self.settings['source-folder']):
            for pattern in self.settings['file-excluding-patterns']:
                if re.search(pattern, fname):
                    break
            else:
                # FIXME если файл успел удалиться
                try:
                    st = os.stat(os.path.join(self.settings['source-folder'], fname))
                except FileNotFoundError:
                    pass
                else:
                    result = {'ino': st.st_ino, 'size': st.st_size, 'stage': 0, 'fname': fname}
                    if is_first:
                        # TODO вставить обработку опережения
                        result['addtime'] = st.st_mtime
                    else:
                        result['addtime'] = time.time()
                    if result['size'] > self.settings['size-cooked']:
                        result['stage'] = 1
                        result['mtime'] = result['addtime']
                    yield result

    # var supply: 0
    def mainloop_cycle(self):
        """самая полезная функция во всём классе

        параметр is_first на случай, если это файлы, который были до запуска проги

        Список смысловых разделов функции:
        - проводит учёт новых файлов
        - удаляет исчезнувшие файлы, если такие были
        - обновляет изменившуюся инфу (размер/имя/...)
        - управляет статусами "готовности" файлов
        - перемещает готовые файлы из cooking в ready
        - двигает файлы, если есть, чего
        - обновляет таймеры изменений (если чото менялось)
        """
        if self.oldfiles:
            self.pause()

        data = list(self.get_directory_content(self.oldfiles))
        data.sort(key = lambda l: l['addtime'])
        inos = [finfo['ino']for finfo in data]
        is_cooking_update = False
        is_ready_update = False
        is_history_update = False
        # --------- register new files
        for finfo in data:
            if finfo['ino'] not in [finfo['ino'] for finfo in it.chain(self.files_cooking, self.files_ready)]:
                self.files_cooking.append(finfo.copy())
                is_cooking_update = True
        
        # --------- check deleted files
        j = 0
        while j < len(self.files_cooking):
            if self.files_cooking[j]['ino'] not in inos:
                del self.files_cooking[j]
                is_cooking_update = True
                j -= 1
            j += 1
        j = 0
        while j < len(self.files_ready):
            if self.files_ready[j]['ino'] not in inos:
                del self.files_ready[j]
                is_cooking_update = True
                j -= 1
            j += 1

        # --------- info update
        for old in self.files_cooking:
            new = data[inos.index(old['ino'])]
            for key in ('fname', 'size'):
                if new[key] != old[key]:
                    old[key] = new[key]
                    is_cooking_update = True
        for old in self.files_ready:
            new = data[inos.index(old['ino'])]
            for key in ('fname', 'size'):
                if new[key] != old[key]:
                    old[key] = new[key]
                    is_ready_update = True
        # --------- check files cooking
        files_to_append = []
        j = 0
        while j < len(self.files_cooking):
            old = self.files_cooking[j]
            new = data[inos.index(old['ino'])]
            if old['stage'] == 0:
                if new['size'] >= self.settings['size-cooked']:
                    old['size'] = new['size']
                    old['stage'] = 1
                    old['mtime'] = time.time()
                    is_cooking_update = True
                    j -= 1
            elif old['stage'] == 1:
                if old['size'] == new['size']:
                    if time.time() - old['mtime'] > self.settings['cooking-time']:
                        old['stage'] = 2
                        is_cooking_update = True
                        j -= 1
                else:
                    old['size'] = new['size']
                    old['mtime'] = new['mtime']
                    is_cooking_update = True
            elif old['stage'] == 2:
                files_to_append.append(self.files_cooking.pop(j))
                is_cooking_update = True
                j -= 1
            j += 1
        # --------- place files into 'cooked' category
        if files_to_append:
            is_ready_update = True
            files_to_append.sort(key=lambda finfo: finfo['addtime'])
            self.files_ready.extend(files_to_append)
            if not self.paused and\
                    self.files_history and\
                    time.time() - self.last_update_time['history'] < \
                    self.settings['seconds-for-overload']:
                self.pause()
        # --------- move files (if there are to)
        if not self.paused and self.files_ready and not self.oldfiles:
            self.file_move()
        # ----------- timers update
        if is_cooking_update:
            self.last_update_time['cooking'] = time.time()
        if is_ready_update:
            self.last_update_time['ready'] = time.time()
        if self.oldfiles:
            self.oldfiles = False
        # TODO invent structure for this work
        # parts:
        # + register new files
        # + check if some files were destroed
        # + check files cooking
        # + send stop sygnal if 2 or more files appeare in N seconds (seconds-for-overload param)
        # - move file if permitted (or create another function for this)
        # + check filename change for READYS

        # - distribute flags updates between UI and FH (main point is who cares about stopping)

    # var supply: +/0
    def validate(self, modifiers):
        """проверяет последовательность кусков имени файла на вшивость
        при левом типе паттерна кидает NotImplementedError"""
        patterns = [x for x in self.settings['name-pattern'] if isinstance(x, list) and x[0] not in ['ext']]
        assert len(modifiers) == len(patterns), (len(modifiers), len(patterns))
        result = [True for m in modifiers]

        for i, (m, p) in enumerate(zip(modifiers, patterns)):
            if p[0] == 'int':
                if not m.isnumeric():
                    # print('i', i, 'not a number')
                    result[i] = False
                elif len(p) > 2 and p[3]:
                    if len(m) != p[1]:
                        # print('i', i, 'len != patlen', len())
                        result[i] = False
                else:
                    if len(m) > p[1]:
                        # print('i', i, 'len > patlen')
                        result[i] = False
            elif p[0] == 'var':
                result[i] = m in p[1]
            else:
                raise NotImplementedError()
        return result

    # var supply: +/0
    def correct(self):
        """меняет вшивые куски имени файла на подходящие невшивые
        при левом типе паттерна кидает NotImplementedError"""

        modifiers = self.ui.get_modifiers()
        patterns = [x for x in self.settings['name-pattern'] if isinstance(x, list) and x[0] not in ['ext']]
        assert len(modifiers) == len(patterns)

        for i, p in enumerate(patterns):
            if p[0] == 'int':
                if not modifiers[i].isnumeric():
                    if modifiers[i]:
                        modifiers[i] = cut_not_digits(modifiers[i])
                    else:
                        modifiers[i] = str(p[2])
                if len(modifiers[i]) > p[1]:
                    modifiers[i] = modifiers[i][:p[1]]
                if len(p) > 2 and p[3] and len(modifiers[i]) < p[1]:
                    modifiers[i] = modifiers[i].zfill(p[1])
            elif p[0] == 'var':
                # print('correct modifier:', p[2])
                if modifiers[i] not in p[1]:
                    modifiers[i] = p[1][p[2]]
            else:
                raise NotImplementedError()
        self.ui.set_modifiers(modifiers)
        self.ui.set_incorrect(self.validate(modifiers))

    # var supply: 0
    def modifiers_apply(self, modifiers, ext):
        """возвращает готовое имя файла
        TODO: вынести ext.lower в файл конфигурации флагом"""
        result = ''
        if COSTYL_PATH:
            result += modifiers[0] + '/'
        i = 0
        for p in self.settings['name-pattern']:
            if isinstance(p, str):
                result += p
            elif isinstance(p, list):
                if p[0] == 'ext':
                    result += ext.lower()
                else:
                    result += modifiers[i]
                    i += 1
        return result

    # var supply: +/-
    def reset(self):
        """сбрасывает все entrys до defaults
        FIXME: будет вести себя плохо, если в var будет '' не на default"""
        self.ui.set_modifiers(['' for x in self.settings['name-pattern'] if isinstance(x, list) and x[0] not in ['ext']])
        self.correct()

    # var supply: +/-
    def modifier_increm(self, index, count, save_others=False):
        """изменяет кусок имени файла с обработками всякий ошибок
        побочный эффект: обращение к UI
        в конце вызывает correct на всякий случай"""
        assert count in (1, -1)
        patterns = [x for x in self.settings['name-pattern'] if isinstance(x, list) and x[0] not in ['ext']]
        intpatterns = [i for i, x in enumerate(patterns) if x[0] == 'int']
        varpatterns = [i for i, x in enumerate(patterns) if x[0] == 'var']

        modifiers = self.ui.get_modifiers()
        for i in intpatterns:
            modifiers[i] = int(modifiers[i])
        # print('modifier_increm ', index)
        # ----------------- change by index
        changes_flag = False
        if patterns[index][0] == 'int':
            newval = modifiers[index] + count
            if newval >= 0 and len(str(newval)) <= patterns[index][1]:
                modifiers[index] += count
                changes_flag = True

        elif patterns[index][0] == 'var':
            vars = patterns[index][1]
            # print('vars:', vars)
            modifiers[index] = vars[(vars.index(modifiers[index]) + count) % len(vars)]
            changes_flag = True
            # print('result:', modifiers[index])
        else:
            raise NotImplementedError()
        # ----------------- change others
        if not save_others and changes_flag:
            for i, p in enumerate(patterns):
                if i > index:
                    if p[0] == 'int':
                        modifiers[i] = p[2]
                    elif p[0] == 'var':
                        modifiers[i] = p[1][p[2]]
                    else:
                        raise NotImplementedError()
            if False:
                for i in range(intpatterns.index(index) + 1, len(intpatterns)):
                    modifiers[intpatterns[i]] = patterns[intpatterns[i]][2]
                for i in varpatterns:
                    if i > index:
                        modifiers[i] = patterns[i][1][patterns[i][2]]
        self.ui.set_modifiers([str(x) for x in modifiers])
        self.correct()
        # print('incremed modifiers', modifiers)

    # var supply: 0
    def ui_setup(self):
        '''вызывается в начале, когда не понятно, что вообще происходит
        (вызывается один раз в конце TkinterFilesHandler._init_2)
        Пока что только синхронизирует статус pause между собой и UI
        todo: выяснить и описать, какой баг перекрывает '''
        self.ui.pause_switch(('resume', 'pause')[self.paused])

    # var supply: 0/0
    def autoincrement(self):
        """выискивает флаг autoincrement и вызывает modifier_increm где надо"""
        patterns = [x for x in self.settings['name-pattern'] if isinstance(x, list) and x[0] not in ['ext']]
        intpatterns = [i for i, p in enumerate(patterns) if p[0]=='int' and p[4]]
        # print('autoincrement', ii)
        if intpatterns:
            self.modifier_increm(intpatterns[0], 1)

    # var supply: 0
    def file_move(self):
        """Вторая важная функция после mainloop_cycle. Надо выяснить и записать, как она работает.
        Работа ф-ции не завивит от состояния флага paused...

        Схема работы:
        Подготовка:
        - копирует текущие modifiers
        - делает autoincrement (нерабочий; FIXME)
        - пытается упасть при invalid modifiers
        - проверяет, есть ли files_ready (если пусто -- конец ф-ции)
        Работа:
        - Применение силы:
            - pop первый в списке files_ready
            - fmove под новым именем из modifiers
        - Коррекция метаданных:
            - добавляем move-time и прочая
            - вызываем функцию history_write, которая ничего не делает)
            - 

        TODO: 
        - обработка invalid_modifiers;
        - добавить finfo['new_ino']
        - вообще написать работу с ino, ну или хотябы выбор...
        - выпилить дурацкое логирование принтами"""

        modifiers = copy.deepcopy(self.ui.get_modifiers())
        # self.modifier_increm(len(modifiers)-1, 1)
        self.autoincrement()
        if not all(self.validate(modifiers)):
            raise ValueError('some modifiers are invalid; write proper logging here')
        if self.files_ready:
            finfo = self.files_ready.pop(0)
            fname = self.modifiers_apply(modifiers, os.path.splitext(finfo['fname'])[-1])
            print('file move', fname)
            fmove(
                os.path.join(self.settings['source-folder'], finfo['fname']),
                os.path.join(self.settings['destination-folder'], fname)
            )
            print('file move -- done')
            finfo['fname-new'] = fname
            finfo['move-time'] = time.time()
            self.files_history.append(finfo)
            self.history_write(json.dumps(finfo))

            self.last_update_time['ready'] = time.time()
            self.last_update_time['history'] = time.time()

        print('FH file move: end of function')  # это вообще чё?

    # var supply: 0
    def history_write(self, s):
        """функция, которая должна с использованием soft_open логировать перемещённые файлы
        TODO: придумать, как при запуске из неё заполнять """
        print('file done:', s)
        if self.settings['history-file'] is not None:
            raise NotImplementedError('write this f; это логирование не работаеть')

    # var supply: 0
    def pause(self):
        """просто self.paused = True, ну ещё обращение к UI с тем же..."""
        self.paused = True
        self.ui.pause_switch('pause')

    # var supply: 0
    def resume(self):
        """if modifiers are invalid -- calls self.ui.set_incorrect;
        if modifiers are valid -- moves file; if no files left -- resumes
        calls ui.resume if ok


        TODO: сделать человекопонятные if-else вместо raise/return"""
        if not self.paused:
            raise Warning('there was nothing to resume...')
        validate_result = self.validate(self.ui.get_modifiers())
        if not all(validate_result):
            self.ui.set_incorrect(validate_result)
            return
        if self.files_ready:
            print('FH resume: file move')
            self.file_move()
            print('FH resume: after file move')
        print('FH resume:', len(self.files_ready))
        if not self.files_ready:
            # ----------------------- successfull resume
            self.paused = False
            self.ui.pause_switch('resume')

    # var supply: 0
    def settings_change(self):
        """not implemented; функция, которая должна решать, какие изменения можна без перезагрузки; валиднуть новые settings и проч"""
        raise NotImplementedError()

if __name__ == '__main__':
    cli = ConsoleUI()
    fh = FilesHandler('settings.json', cli)
    while True:
        fh.mainloop_cycle()
        pprint.pprint(fh.files_cooking)
        pprint.pprint(fh.files_ready)
        print('-'*30)
        time.sleep(1)

