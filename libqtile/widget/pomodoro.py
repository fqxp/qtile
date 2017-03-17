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
import logging
import os.path
import shutil
import time


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
    ]

    def __init__(self, **config):
        base.InLoopPollText.__init__(self, **config)
        self.add_defaults(Pomodoro.defaults)
        self._running = False
        self.foreground = self.not_running_text_color

    def tick(self):
        self._update_view()

    def button_press(self, x, y, button):
        if button == 1:
            self.cmd_toggle()

    def cmd_toggle(self):
        if self._running:
            self.cmd_stop()
        else:
            self.cmd_start()

    def cmd_start(self):
        self.cmd_start_interval('work')
        self._running = True
        self._update_view()

    def cmd_stop(self):
        self._running = False
        self.foreground = self.not_running_text_color
        self._update_view()

    def cmd_start_interval(self, mode):
        self._started_at = time.monotonic()

        if mode == 'work':
            self._mode = 'work'
            self._current_interval = self.work_interval * 60
            self.foreground = self.work_text_color
        else:
            self._mode = 'rest'
            self._current_interval = self.rest_interval * 60
            self.foreground = self.rest_text_color

        self._play_sound(self._mode)

    def cmd_next_interval(self):
        if self._mode == 'work':
            next_interval = 'rest'
        else:
            next_interval = 'work'

        self.cmd_start_interval(next_interval)

    def _update_view(self):
        if self._running:
            remaining_time = self._remaining_time(self._started_at, self._current_interval)

            if remaining_time < 1.0:
                self.cmd_start_interval('work' if self._mode == 'rest' else 'rest')
                remaining_time = self._current_interval

            self.update('%s %s' % (
                self._formatted_mode(self._mode),
                self._formatted_time(remaining_time)))
        else:
            self.update(self.not_running_text)

    def _play_sound(self, mode):
        sound = self.work_sound if mode == 'work' else self.rest_sound
        if not os.path.exists(sound):
            logger.error('Pomodoro: sound file %s does not exist' % sound)
            return

        if not shutil.which(self.play_sound_command):
            logger.error('Pomodoro: command "%s" not found in path' % self.play_sound_command)
            return

        self.qtile.cmd_spawn([self.play_sound_command, sound])

    def _remaining_time(self, started_at, interval):
        return started_at + interval - time.monotonic()

    def _formatted_mode(self, mode):
        if mode == 'work':
            return self.work_text
        else:
            return self.rest_text

    def _formatted_time(self, seconds):
        return '%d:%02d' % divmod(seconds, 60)
