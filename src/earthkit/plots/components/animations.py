# Copyright 2024-, European Centre for Medium Range Weather Forecasts.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import matplotlib.animation as animation

from earthkit.plots.components.figures import Figure


class Animation(Figure):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._frame_data = []
        self._subplot_titles = None

    def contourf(self, data, *args, **kwargs):
        super().contourf(data[0], *args, **kwargs)
        for d in data:
            self._frame_data.append(d)

    def subplot_titles(self, label, *args, **kwargs):
        super().subplot_titles(label, *args, **kwargs)
        self._subplot_titles = label

    def update(self, frame):
        if self._frame_data:
            data = self._frame_data[frame]
            self.subplots[0].ax.clear()
            self.subplots[0].layers = []
            self.subplots[0].contourf(data)
            if self._subplot_titles:
                self.subplot_titles(self._subplot_titles)

    def show(self, interval=100):
        # self._release_queue()

        ani = animation.FuncAnimation(
            fig=self.fig,
            func=self.update,
            frames=len(self._frame_data),
            interval=interval,
        )
        return ani.to_html5_video()
