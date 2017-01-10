#  Copyright 2017 Peter Williams <pwil3058@gmail.com>
#
# This software is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License only.
#
# This software is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this software; if not, write to:
#  The Free Software Foundation, Inc., 51 Franklin Street,
#  Fifth Floor, Boston, MA 02110-1301 USA

"""Take screen samples
"""

import shutil
import subprocess
import sys

from . import dialogue

__all__ = []
__author__ = "Peter Williams <pwil3058@gmail.com>"

GNOME_SCREENSHOT = shutil.which("gnome-screenshot")

def take_screen_sample():
    if sys.platform.startswith("win"):
        dlg = dialogue.MessageDialog(text=_("Functionality NOT available on Windows. Use built in Clipping Tool."))
        dlg.run()
        dlg.destroy()
        return None
    elif GNOME_SCREENSHOT is not None:
        return subprocess.run([GNOME_SCREENSHOT, "-ac"])
    else:
        dlg = dialogue.MessageDialog(text=_("Functionality requires \"gnome-screenshot\" to be installed."))
        dlg.run()
        dlg.destroy()
        return None
