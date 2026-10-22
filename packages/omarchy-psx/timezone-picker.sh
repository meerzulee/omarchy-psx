#!/usr/bin/env bash
# Sourced after the pinned upstream setup form. Only defines the psX prompts;
# loading this file never configures the clock or writes system files.

omarchy_gmt_timezone_rows() {
  local offset zone
  for (( offset = -12; offset <= 14; offset++ )); do
    case $offset in
      0) zone=Etc/UTC ;;
      -*) zone="Etc/GMT+${offset#-}" ;;
      *) zone="Etc/GMT-$offset" ;;
    esac
    # tzdata's Etc/GMT signs follow POSIX, opposite to the user-facing offset.
    printf 'GMT%+03d:00\t%s\n' "$offset" "$zone"
  done
}

omarchy_prompt_timezone_by_location() {
  local region='' location='' status=0
  local timezones='' regions='' guessed_region='' guessed_location=''
  local -a choose_args=()

  timezones=$(timedatectl --no-pager list-timezones) || return $?
  [[ -n $timezones ]] || timezones=UTC
  # Reuse a previous choice, without a network-dependent location lookup.
  if [[ -n ${timezone:-} ]] && grep -Fxq -- "$timezone" <<<"$timezones"; then
    guessed_region=${timezone%%/*}
    [[ $timezone != */* ]] || guessed_location=${timezone#*/}
  fi

  regions=$(awk -F/ 'NF { print $1 }' <<<"$timezones" | sort -u)
  choose_args=(--height 10 --header 'World region (Up/Down to scroll)')
  [[ -z $guessed_region ]] || choose_args+=(--selected "$guessed_region")
  render_setup_step 'TIMEZONE' 'Choose your world region.'
  region=$(gum choose "${choose_args[@]}" <<<"$regions") && status=0 || status=$?
  (( status == 0 )) || return "$status"
  grep -Fxq -- "$region" <<<"$regions" || return 1

  if grep -Fxq -- "$region" <<<"$timezones"; then
    timezone=$region
    timezone_label=$region
    return 0
  fi

  choose_args=(--height 10 --header "$region (Up/Down to scroll)")
  [[ -z $guessed_location ]] || choose_args+=(--selected "$guessed_location")
  render_setup_step 'TIMEZONE' "Choose a timezone in $region."
  location=$(awk -v prefix="$region/" 'index($0, prefix) == 1 { print substr($0, length(prefix) + 1) }' \
    <<<"$timezones" | gum choose "${choose_args[@]}") && status=0 || status=$?
  (( status == 0 )) || return "$status"
  grep -Fxq -- "$region/$location" <<<"$timezones" || return 1

  timezone="$region/$location"
  timezone_label=$timezone
}

omarchy_prompt_timezone() {
  local rows='' choices='' choice='' zone='' status=0 selected='GMT+00:00'
  local location_option='Choose by city or region...'

  rows=$(omarchy_gmt_timezone_rows)
  choices=$(cut -f1 <<<"$rows")
  if [[ -n ${timezone_label:-} ]] && grep -Fxq -- "$timezone_label" <<<"$choices"; then
    selected=$timezone_label
  elif [[ -n ${timezone:-} && $timezone != Etc/* ]]; then
    selected=$location_option
  fi
  choices="$location_option"$'\n'"$choices"

  # A bounded Gum list avoids the live filter's Linux-VT repaint artifacts.
  render_setup_step 'TIMEZONE' 'GMT stays fixed. Choose a city for daylight saving or :30/:45.'
  choice=$(gum choose --height 10 --header 'GMT offset (Up/Down to scroll)' \
    --selected "$selected" <<<"$choices") && status=0 || status=$?
  (( status == 0 )) || return "$status"
  if [[ $choice == "$location_option" ]]; then
    omarchy_prompt_timezone_by_location
    return $?
  fi

  zone=$(awk -F '\t' -v label="$choice" '$1 == label { print $2 }' <<<"$rows")
  [[ -n $zone ]] || return 1
  timezone=$zone
  timezone_label=$choice
}
