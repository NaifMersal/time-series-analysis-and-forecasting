function Header(h)
  if h.classes:includes("splash") then
    h.attributes["background-image"] = "{{< brand logo anim >}}"
    h.attributes["background-opacity"] = "0.1"
  end
  return h
end
