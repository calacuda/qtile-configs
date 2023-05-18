# Copyright (c) 2010 Aldo Cortesi
# Copyright (c) 2010, 2014 dequis
# Copyright (c) 2012 Randall Ma
# Copyright (c) 2012-2014 Tycho Andersen
# Copyright (c) 2012 Craig Barnes
# Copyright (c) 2013 horsik
# Copyright (c) 2013 Tao Sauvage
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

from libqtile import qtile
from libqtile import bar, layout, widget, hook
from libqtile.config import Click, Drag, Group, Key, Match, Screen
from libqtile.backend.wayland import InputConfig
from libqtile.lazy import lazy
from libqtile.core.manager import Qtile
# from gi.repository import Notify
from logger import Logger as FuncLog
from libqtile.log_utils import logger
import api  # not used but a necessary import
import os
import netifaces

HOME = os.path.expanduser('~/')
DEBUG = True
LOGGER = FuncLog(
    debug=DEBUG,
    logging=True,
    io_stream=None,
    log_file=HOME + ".local/share/qtile/qtile_user_funciton.log"
)


######################
# user def lazy func #
######################


def motd():
    """gets the message of the day"""
    motd_path = "/etc/motd"

    if os.path.exists(motd_path):
        with open(motd_path, "r") as motd_f:
            # print(motd_f.read().strip())
            return motd_f.read().strip().replace("\n", "")
    else:
        # print("foobar")
        # print("MOTD error, missing file")
        return "MOTD error, missing file"


def _get_bat_level():
    """
    returns a tuple containing the battery percent and powersource
    i.e (charging or discharging)
    """
    import psutil

    battery = psutil.sensors_battery()
    # battery.power_plugged will be true when the laptop is unplugged ??? WHY!
    charging = battery.power_plugged
    seconds = battery.secsleft
    time_left = convert_time(seconds)

    return (battery.percent, charging, time_left, seconds)


def convert_time(seconds):
    """
    function returning time in hh:mm
    from: https://www.geeksforgeeks.org/python-script-to-shows-laptop-battery-percentage/
    """
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    # return "%d:%02d:%02d" % (hours, minutes, seconds)
    return "%d:%02d" % (hours, minutes)


def bat_notif(title="Battery:  {bat}% ({state})", message_lines=["~{time_left} op time left...", "estimated total battery life. ~{battery_capacity}..."]):
    import dbus

    bus_name = "org.freedesktop.Notifications"
    object_path = "/org/freedesktop/Notifications"
    interface = bus_name

    notify = dbus.Interface(dbus.SessionBus().get_object(
        bus_name, object_path), interface)
    perc, charging, time_left, seconds = _get_bat_level()
    bat_cap = convert_time(seconds/(perc/100))
    state = "Charging" if charging else "Discharging"
    time_left = time_left if not charging else "inf"

    message = "\n".join([line.format(bat=round(perc, 1), state=state, time_left=time_left, battery_capacity=bat_cap)
                        for line in message_lines])

    notify.Notify(
        "bat-notif", 0, "",  # first string is the app name
        title.format(bat=round(perc, 1), state=state, time_left=time_left),
        message,
        [],
        {"urgency": 1},
        3500
    )


@lazy.function
def lazy_bat_notif(qtile):
    """lazy function wrapper for bat_notif"""
    if qtile.core.name == "x11":
        # bat_notif("Battery:  {bat}% ({state})", ["~{time_left} op time left"])
        bat_notif(
            "Battery:  {bat}% ({state})", [
                "~{time_left} op time left",
                "~{battery_capacity} estimated total battery life."
            ]
        )


@lazy.function
def lazy_sh(qtile, app):
    """lazy spawn an app in a subprocess."""
    os.system(app)


# @lazy.function
def go_to_group(name: str):
    def _inner(qtile):
        # logger.error("calling _inner")
        if len(qtile.screens) == 1:
            qtile.groups_map[name].cmd_toscreen()
            return

        if name in '1234567':
            qtile.focus_screen(0)
            qtile.groups_map[name].cmd_toscreen()
        else:
            qtile.focus_screen(1)
            qtile.groups_map[name].cmd_toscreen()

    return _inner


######################
# Keyboard shortcuts #
######################


mod = "mod4"  # Super key
alt_key = "mod1"  # ALT KEY?

terminal = "alacritty"  # "kitty"  # guess_terminal()

keys = [
    # A list of available commands that can be bound to keys can be found
    # at https://docs.qtile.org/en/latest/manual/config/lazy.html
    # Switch between windows
    Key([mod], "Left", lazy.layout.left(), desc="Move focus to left"),
    Key([mod], "Right", lazy.layout.right(), desc="Move focus to right"),
    Key([mod], "Down", lazy.layout.down(), desc="Move focus down"),
    Key([mod], "Up", lazy.layout.up(), desc="Move focus up"),
    # Key([mod], "space", lazy.layout.next(), desc="Move window focus to other window"),
    # Move windows between left/right columns or move up/down in current stack.
    # Moving out of range in Columns layout will create new column.
    Key([mod, "shift"], "Left", lazy.layout.shuffle_left(),
        desc="Move window to the left"),
    Key([mod, "shift"], "Right", lazy.layout.shuffle_right(),
        desc="Move window to the right"),
    Key([mod, "shift"], "Down", lazy.layout.shuffle_down(), desc="Move window down"),
    Key([mod, "shift"], "Up", lazy.layout.shuffle_up(), desc="Move window up"),
    # Grow windows. If current window is on the edge of screen and direction
    # will be to screen edge - window would shrink.
    Key([mod, "control"], "Left", lazy.layout.grow_left(),
        desc="Grow window to the left"),
    Key([mod, "control"], "Right", lazy.layout.grow_right(),
        desc="Grow window to the right"),
    Key([mod, "control"], "Down", lazy.layout.grow_down(), desc="Grow window down"),
    Key([mod, "control"], "Up", lazy.layout.grow_up(), desc="Grow window up"),
    Key([mod], "n", lazy.layout.normalize(), desc="Reset all window sizes"),
    Key([mod, "control"], "r", lazy.reload_config(), desc="Reload the config"),
    # Toggle between different layouts as defined below
    Key([mod], "Tab", lazy.next_layout(), desc="Toggle between layouts"),
    # Key([mod, "control"], "q", lazy.shutdown(), desc="Shutdown Qtile"),
    Key([mod], "x", lazy.window.kill(), desc="Kill focused window"),
    Key([mod], "f", lazy.window.toggle_fullscreen(), desc="Toggle fullscreen"),
    Key([mod], "t", lazy.window.toggle_floating(), desc='Toggle floating'),

    # Toggle between split and unsplit sides of stack.
    # Split = all windows displayed
    # Unsplit = 1 window displayed, like Max layout, but still with
    # multiple stack panes
    # Key(
    #     [mod, "shift"],
    #     "Return",
    #     lazy.layout.toggle_split(),
    #     desc="Toggle between split and unsplit sides of stack",
    # ),

    Key([mod], "Return", lazy.spawn(terminal), desc="Launch terminal"),
    Key([mod], "e", lazy.spawn("codium"), desc="Open editor"),
    # Key([mod], "d", lazy.spawn("autorandr -l default"),
        # desc="Return to laptop mode"),
    Key([mod], "r", lazy.spawn(
        f"{HOME}.cargo/bin/auto-desk launch {HOME}Code/python/mimic3-speak/mimic3-speak_v3.py"), desc="Read the highlighted text"),
    Key([mod], "t", lazy.spawn("/usr/bin/rofi-bluetooth"),
        desc="Show bluetooth menu"),
    Key([mod], "w",
        lazy.spawn(
            "rofi -modi \"clipboard:greenclip print\" -show clipboard -run-command '{cmd}'"),
        desc="Show clipboard"),
    Key([mod], "space",
        lazy.spawn(
            "rofi -modi \"Apps\":\"~/.config/bspwm/scripts/rofi-favorites.sh\" -show \"Apps\" -drun-display-format \" -> {name}\""),
        desc="Rofi favorites"),
    Key([mod], "b", lazy.spawn("firefox"), desc="Spawn web browser"),
    # Key([mod], "p", lazy.spawncmd(), desc="Spawn a command using a prompt widget"),
    Key([mod, "shift"], "space", lazy.spawn(
        "rofi -show drun -drun-display-format \" -> {name}\""), desc="Show app launcher"),
    # Key([mod, "shift"], "p", lazy.spawn("alacritty -e parufzf"), desc="parufzf"),
    Key([mod, "shift"], "Return", lazy.spawn(
        "pcmanfm-qt"), desc="Spawn file browser"),
    Key([mod], "F12", lazy.spawn("rofi-wifi-menu"), desc="Show wifi menu"),
    Key([mod], "F11", lazy.spawn("/usr/bin/rofi-bluetooth"),
        desc="Show bluetooth menu"),
    Key([mod], "Print", lazy.spawn("flameshot gui"),
        desc="Take a screenshot (flameshot)"),
    Key([mod, "mod1"], "Escape", lazy.spawn(
        "rofi -modi \"Power\":\"rofi-power-menu\" -show \"Power\""), desc="Power/Logout menu"),
    Key([mod], "s", lazy_bat_notif, desc="Check battery level"),
    Key([mod], "v", lazy.spawn("pavucontrol"), desc="audio volume mixer"),
    Key([alt_key], "c", lazy.spawn("xdotool key Caps_Lock"),
        desc="TOGLE CAPSLOCK (as you can see this is important)"),
    Key([mod, "shift"], "p", lazy.spawn(terminal + \
        f" -e {HOME}.local/bin/parufzf"), desc="TUI for paru"),

    # Media/fn-keys stuff
    Key([], "XF86AudioRaiseVolume", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume up')), desc="Raise the volume"),
    Key([], "XF86AudioLowerVolume", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume down')), desc="Lower the volume"),
    Key([], "XF86AudioMute", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume mute')), desc="Mute the volume"),
    Key([], "XF86AudioMedia", lazy.spawn("lollypop"), desc="launch media player"),
    # lazy.function(lambda qtile: os.system(
    # 'bash ~/.config/system_scripts/volume pause')), desc="Pasue media"),
    Key([], "XF86AudioPlay", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume pause')), desc="Play media"),
    Key([], "XF86AudioPrev", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume prev')), desc="Previous track"),
    Key([], "XF86AudioNext", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/volume next')), desc="Next track"),
    Key([], "XF86MonBrightnessUp", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/brightness up')), desc="increase screen brightness"),
    Key([], "XF86MonBrightnessDown", lazy.function(lambda qtile: os.system(
        'bash ~/.config/system_scripts/brightness down ')), desc="Lower screen brightness"),
    # Key([], "", lazy.function(lambda qtile: os.system('bash ~/.config/system_scripts/volume ')), desc=""),
]


#############################################
# Groups (and kayboard shorcuts for groups) #
#############################################


groups = [Group(str(i)) for i in range(1, 11)]  # "123456789"]

for i in groups:
    k = str(int(i.name) % 10)
    # k = i.name if i.name != "10" else "0"
    # k = i.name if int(i.name) != 10 else "0"
    keys.extend(
        [
            # mod1 + letter of group = switch to group
            Key(
                [mod],
                k,
                # lazy.group[i.name].toscreen(),
                lazy.function(go_to_group(i.name)),
                desc="Switch to group {}".format(i.name),
            ),
            # mod1 + shift + letter of group = move focused window to group
            Key([mod, "shift"], k, lazy.window.togroup(i.name),
                desc="move focused window to group {}".format(i.name)),
        ]
    )

groups.append(Group("hidden"))

layouts = [
    # layout.Columns(border_focus_stack=["#d75f5f", "#8f3d3d"], border_width=4),
    # layout.Max(),
    # Try more layouts by unleashing below layouts.
    # layout.Bsp(),
    # layout.Stack(num_stacks=2),
    # layout.Matrix(),
    layout.MonadTall(
        border_focus="#f9e2af",  # "#D09D49",
        border_normal="#89dceb",  # "#45778B",
        border_focus_stack=["#d75f5f", "#8f3d3d"],
        border_width=3,
        margin=6,
        # any larger and it will interfear with the pokedex fetch
        # program I use, on my 4:3 AR laptop screen.
        ratio=0.56
    ),
    layout.MonadWide(
        border_focus="#f9e2af",  # "#D09D49",
        border_normal="#89dceb",  # "#45778B",
        border_focus_stack=["#d75f5f", "#8f3d3d"],
        border_width=3,
        margin=6,
        ratio=0.56
    ),
    # layout.RatioTile(),
    # layout.Tile(),
    # layout.TreeTab(),
    # layout.VerticalTile(),
    # layout.Zoomy(),
]

widget_defaults = dict(
    font="sans",
    fontsize=16,
    padding=4,
)

extension_defaults = widget_defaults.copy()
interface = None

for face in netifaces.interfaces():
    if face.startswith("wl"):
        interface = face
        break

# # wallpaper = '~/Pictures/backgrounds/catppuccin/windows-error.jpg'
# wallpaper = '~/Pictures/backgrounds/catppuccin/catppuccin_triangle.png'
# wallpaper = '~/Pictures/backgrounds/catppuccin/car-2.jpg'
# wallpaper = '~/Pictures/backgrounds/catppuccin/cat-sound.png'
# wallpaper = '~/Pictures/backgrounds/catppuccin/cat_colors.png'
# wallpaper = '~/Pictures/backgrounds/catppuccin/rainbow-cat.png'
# wallpaper = '~/Pictures/backgrounds/catppuccin/Street.jpg'
# wallpaper = '~/Pictures/backgrounds/catppuccin/spooky_spill.jpg'

wallpaper = '~/.config/qtile/wallpapers/cat_leaves.png'
# wallpaper = '~/.config/qtile/wallpapers/spooky_spill.jpg'
# wallpaper = "~/Code/git-repos/sway-dots/wallpapers/cyborg_gruv.png"

# wallpaper = '~/Pictures/backgrounds/Dragon.jpg'
wp_mode = "fill"

main_bar = bar.Bar(
    [
        widget.Spacer(length=10),
        # widget.Pomodoro(num_pomodori=3),
        widget.GroupBox(highlight_method='block',
                        visible_groups=[
                            g.name for g in groups if g.name.isnumeric()],
                        active="#fab387",
                        inactive="#585b70",
                        this_current_screen_border="#215578",
                        ),
        # widget.Prompt(background="#000000"),
        widget.Spacer(),
        widget.Clock(format="%a %I:%M %p", foreground="#fab387"),
        widget.Spacer(),
        widget.GenPollText(func=motd, scroll=True, scroll_interval=.05,
                           scroll_clear=False, scroll_delay=3,
                           update_interval=None, width=300,
                           foreground="#fab387"),
        widget.Spacer(length=15),
        # widget.Systray(),
        widget.Spacer(length=15),
        widget.Battery(
            format='{char} {percent:2.0%} {watt:.2f} W', foreground="#fab387"),
        # widget.QuickExit(),
        widget.Spacer(length=10),
    ],
    40,
    background="#11111bCC",
    margin=6
)

screens = [
    Screen(
        top=main_bar,
        wallpaper=wallpaper,  # '~/Pictures/backgrounds/Dragon.jpg',
        wallpaper_mode=wp_mode,  # 'stretch',
    )
]

# Drag floating layouts.
mouse = [
    Drag([mod], "Button1", lazy.window.set_position_floating(),
         start=lazy.window.get_position()),
    Drag([mod], "Button3", lazy.window.set_size_floating(),
         start=lazy.window.get_size()),
    Click([mod], "Button2", lazy.window.bring_to_front()),
]

dgroups_key_binder = None
dgroups_app_rules = []  # type: list
follow_mouse_focus = True
bring_front_click = False
cursor_warp = False
floating_layout = layout.Floating(
    float_rules=[
        # Run the utility of `xprop` to see the wm class and name of an X client.
        *layout.Floating.default_float_rules,
        Match(wm_class="confirmreset"),  # gitk
        Match(wm_class="makebranch"),  # gitk
        Match(wm_class="maketag"),  # gitk
        Match(wm_class="ssh-askpass"),  # ssh-askpass
        Match(wm_class="matplotlib"),  # matplotlib plots
        Match(title="branchdialog"),  # gitk
        Match(title="pinentry"),  # GPG key password entry
    ]
)
# auto_fullscreen = False
auto_fullscreen = True
focus_on_window_activation = "smart"
reconfigure_screens = True

# If things like steam games want to auto-minimize themselves when losing
# focus, should we respect this or not?
auto_minimize = True

# When using the Wayland backend, this can be used to configure input devices.
# wl_input_rules = None
wl_input_rules = {
    "type:keyboard": InputConfig(kb_options="caps:super"),
}
# wl_input_rules = None

# XXX: Gasp! We're lying here. In fact, nobody really uses or cares about this
# string besides java UI toolkits; you can see several discussions on the
# mailing lists, GitHub issues, and other WM documentation that suggest setting
# this string if your java app doesn't work correctly. We may as well just lie
# and say that we're a working one by default.
#
# We choose LG3D to maximize irony: it is a 3D non-reparenting WM written in
# java that happens to be on java's whitelist.
wmname = "LG3D"


#########
# Hooks #
#########

@hook.subscribe.startup_once
def autostart():
    """runs the autostart shell script"""
    import subprocess

    home = os.path.expanduser('~')
    subprocess.Popen([home + '/.config/qtile/autostart.sh'])


# @hook.subscribe.client_new
# def open_on(c):
#     """auto-relocates windows if there is a defined location in /tmp/qtile/locations"""
#     # import json

#     # data_path = "/tmp/qtile/locations.json"
#     pid = c.get_pid()

#     # this function gets called twice per window opening.
#     # bellow stops this function from moving windows that have already been moved.
#     if pid in PIDs:
#         PIDs.remove(pid)
#         return

#     # with API.lock:
#     if API.rules:
#         PIDs.add(pid)
#         # could use get_pid() and then use that to get executable and just store the executable in locations
#         names = c._wm_class
#         # makes the code more stable in case a malformed message has a program but no location.
#         location = None
#         for wm_class in names:
#             location = API.get_location(wm_class)
#             if location is not None:
#                 break
#         if location:
#             # windows = []
#             c.togroup(location)
#             # for window in windows:
#             #     window.togroup("hidden")


@hook.subscribe.startup_once
def greet_user():
    """notifies the user of the batery level when they login"""
    if qtile.core.name == "x11":
        bat_notif(f"Greetings  {os.getlogin().title()}",
                  ["Battery:  {bat}% & {state}"])


@hook.subscribe.shutdown
def autostop():
    """runs the auto stop shell script"""
    import subprocess

    # API.stop_api()
    home = os.path.expanduser('~')
    subprocess.Popen([home + '/.config/qtile/autostop.sh'])


# relload config on screen change. uncomment "@hook.subscribe.screen_change
@hook.subscribe.screen_change
# @LOGGER.log
def reload_config(randr_event):
    """
    reloads the configs when new monitors are activated.
    (for example by autorandr)
    """
    import signal

    # sends SIGUSR1 to qtile to restart it
    # side not: (why does python not have a dedicated signal sending function?)
    if get_n_mon() != len(screens):
        add_screens_x()
        os.kill(os.getpid(), signal.SIGUSR1)
        # add_screens_x()
        return True
    else:
        return False


@hook.subscribe.startup_once
async def autorandr():
    """autorandrs on start"""
    # import subprocess

    # subprocess.Popen(['autorandr -c'])
    if qtile.core.name == "x11":
        os.system("autorandr -c")


def make_fullscreen(target, client):
    """forces wm_class to be full screen"""
    if target in client.get_wm_class():
        client.fullscreen = True


# @hook.subscribe.client_new
# async def fullscreen_vs_code(client):
#     """
#     makes vs-code (code-oss) full screen always
#     """
#     make_fullscreen("code-oss", client)


# @hook.subscribe.client_new
# async def fullscreen_proxmox(client):
#     """
#     makes proxmox full screen always
#     """
#     make_fullscreen("proxmox-nativefier-0d5e90", client)


##################
# Misc Functions #
##################

def get_n_mon():
    """returns the number of attached monitors"""
    # import gi
    # gi.require_version("Gdk", "3.0")
    # from gi.repository import Gdk

    # gdkdsp = Gdk.Display.get_default()
    # n_mons = gdkdsp.get_n_monitors()

    # return n_mons
    from screeninfo import get_monitors

    return len(get_monitors())


# @LOGGER.log
def add_screens_x():
    """called to add 1 default screen to the screens list for every attached monitor"""
    # if os.getenv('XDG_SESSION_TYPE').lower() == "wayland":
    if qtile.core.name != "x11":
        return

    global screens

    n_mon = get_n_mon()
    n_screens = len(screens)

    if n_mon > n_screens:
        for _ in range(n_mon - n_screens):
            screens.append(
                Screen(top=None, wallpaper=wallpaper, wallpaper_mode=wp_mode))
    elif n_mon < n_screens:
        screens[0:n_mon - 1]
    else:
        return False

    return (n_mon, n_screens, len(screens))


#########
# start #
#########

if __name__ == "__main__":
    pass
    # add doctest.testmod stuff
else:
    if qtile.core.name == "x11":
        add_screens_x()
