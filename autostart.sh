#!/bin/bash

function run {
  if ! pgrep $1 ;
  then
    $@ &
  fi
}

# function activate_monitors {
#   mon1con="$(xrandr -q | grep 'DP3-1 connected')"
#   mon2con="$(xrandr -q | grep 'DP3-2 connected')"

#   if [[ $mon1con && $mon2con ]]; then  # this makes login faster when no monitor is attached
#     # this is so that an xrandr is actually triggered that way Qtile events will actually be triggered. 
#     # autorandr -l default
#     autorandr -c
#     autorandr -fl docked
#   fi
# }

function super-user-set-up {
  doas /usr/bin/chmod 0666 /dev/null &
  doas /usr/bin/chmod 0666 /dev/ptmx &
  doas /usr/bin/chmod 0666 /dev/tty  &
  # doas /usr/bin/powertop --auto-tune &
}

function radio-freq-set-up {
  rfkill unblock wifi &
  rfkill unblock bluetooth &
  bluetooth off &
}

function start-home-screen {
  docker run -it -d -p 127.0.0.1:80:8080 -v ~/Code/git-repos/bento-next/config.ts:/usr/share/nginx/html/config.ts bento-next
}

# xrandr --dpi 160; xrandr --dpi 160 &
super-user-set-up &
radio-freq-set-up &

xinput set-prop "11" "libinput Click Method Enabled" 0 1 &  # allows two finger click to be a right click.
# kdeconnect-cli --refresh &
tmux -L bug-bounty new echo "nothing" &  # just to start a server running on a socket named bug-bounty
nm-applet &  # needed for protonvpn to work

# remap keys
xmodmap ~/.xmodmaprc & 
setxkbmap -option caps:super &
# setxkbmap -option caps:ctrl_modifier &

numlockx on &
blueberry-tray &
kdeconnect-indicator &
# picom --experimental-backends -b &
picom -b &
numlockx on &
# mailspring -b &
/usr/lib/polkit-gnome/polkit-gnome-authentication-agent-1 &
# bash ~/.config/bspwm/scripts/bg.sh ~/Pictures/backgrounds/animated/pixilated_animated_1.gif
batsignal -w 15 -c 10 -d 7 -m 180 -D 'systemctl hibernate' -b &
systemctl start --user auto-desk.service &
systemctl restart --user greenclip &
xss-lock -- betterlockscreen -l -q > /dev/null &
mkdir -p /tmp/qtile/ & 
python -m frankentile.web 10.42.69.3 & 
python -m frankentile.discord_bot &
doas nebula -config /etc/nebula/config.yml &
wmcompanion &
start-home-screen &
# activate_monitors &
# glava -d > /dev/null &
# xcape -t 250 -e 'Super_L=Super_R|space' &
