# -*- coding: utf-8 -*-
# Copyright (c) 2017 Frank Ploss
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

from libqtile.log_utils import logger
from libqtile.widget import base
import datetime
import os
import os.path
import shutil


class Pomodoro(base.InLoopPollText):

    defaults = [
        ('work_interval', 25, 'Length of work interval in minutes'),
        ('rest_interval', 5, 'Length of rest interval in minutes'),
        ('update_interval', 1., 'Update interval'),
        ('not_running_text', u'🍅', 'Text to show when timer is not running'),
        ('not_running_text_color', 'bbbbbb', 'Text color when timer is not running'),
        ('work_text', 'work', 'Text to show in work interval'),
        ('work_text_color', 'ffffff', 'Text color in work interval'),
        ('rest_text', 'rest', 'Text to show in rest interval'),
        ('rest_text_color', 'ff4444', 'Text color in rest interval'),
        ('work_sound', '/usr/share/sounds/freedesktop/stereo/complete.oga', 'Sound to play when starting work interval'),
        ('rest_sound', '/usr/share/sounds/freedesktop/stereo/alarm-clock-elapsed.oga', 'Sound to play when starting rest interval'),
        ('play_sound_command', 'paplay', 'Command to play sound'),
        ('state_filename', os.path.expanduser('~/.local/share/qtile/pomodoro.timer')),
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(Pomodoro.defaults)
        self._restore_start_time()
        self._mode = None
        self._remaining_time = None
        self._update_state(silent=True)

    def cmd_toggle(self):
        if self._is_running():
            self.cmd_stop()
        else:
            self.cmd_start()

    def cmd_start(self):
        self._start_time = int(datetime.datetime.now().timestamp())
        self._persist_start_time()
        self._update_state()
        self._update_view()

    def cmd_stop(self):
        self._start_time = None
        self._persist_start_time()
        self._update_view()

    def tick(self):
        self._update_state()
        self._update_view()

    def button_press(self, x, y, button):
        if button == 1:
            self.cmd_toggle()

    def _update_state(self, silent=False):
        if self._is_running():
            (previous_mode, previous_remaining_time) = (self._mode, self._remaining_time)
            (self._mode, self._remaining_time) = self._current_state(self._start_time)

            if previous_remaining_time == 1 and self._mode != previous_mode:
                self._play_sound(self._mode)
        else:
            self._mode = None
            self._remaining_time = None

    def _update_view(self):
        if self._is_running():
            if self._mode == 'work':
                self.foreground = self.work_text_color
            elif self._mode == 'rest':
                self.foreground = self.rest_text_color

            self.update('%s %s' % (
                self._formatted_mode(self._mode),
                self._formatted_time(self._remaining_time)))
        else:
            self.foreground = self.not_running_text_color
            self.update(self.not_running_text)

    def _play_sound(self, mode):
        sound = self.work_sound if mode == 'work' else self.rest_sound
        if not os.path.exists(sound):
            logger.error('Sound file %s does not exist' % sound)
            return

        if not shutil.which(self.play_sound_command):
            logger.error('Command "%s" not found in path' % self.play_sound_command)
            return

        self.qtile.cmd_spawn([self.play_sound_command, sound])

    def _persist_start_time(self):
        if self._is_running():
            with open(self.state_filename, 'w') as fd:
                print('%d' % self._start_time, file=fd)
        else:
            if os.path.exists(self.state_filename):
                os.remove(self.state_filename)

    def _restore_start_time(self):
        if os.path.exists(self.state_filename):
            try:
                with open(self.state_filename, 'r') as fd:
                    self._start_time = int(fd.read())
            except Exception as e:
                logger.error('Couldn’t restore start time (%s)' % str(e))
                self._start_time = None
        else:
            self._start_time = None

    def _current_state(self, started_at):
        now = int(datetime.datetime.now().timestamp())
        total_interval_seconds = (self.work_interval + self.rest_interval) * 60
        current_interval_seconds = (now - self._start_time) % total_interval_seconds

        if current_interval_seconds < self.work_interval * 60:
            return ('work', self.work_interval * 60 - current_interval_seconds)
        else:
            return ('rest', self.rest_interval * 60 - (current_interval_seconds - self.work_interval * 60))

    def _is_running(self):
        return self._start_time is not None

    def _formatted_mode(self, mode):
        if mode == 'work':
            return self.work_text
        else:
            return self.rest_text

    def _formatted_time(self, seconds):
        return '%d:%02d' % divmod(seconds, 60)
