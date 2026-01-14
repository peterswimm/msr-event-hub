import React, { useState } from "react";
import { Menu, MenuItem, MenuList, MenuPopover, MenuTrigger, Button } from "@fluentui/react-components";
import { Navigation24Regular } from "@fluentui/react-icons";

interface HamburgerMenuProps {
  onMenuItemClick: (action: string) => void;
}

const HamburgerMenu: React.FC<HamburgerMenuProps> = ({ onMenuItemClick }) => {
  const [open, setOpen] = useState(false);

  const handleItemClick = (action: string) => {
    setOpen(false);
    onMenuItemClick(action);
  };

  return (
    <Menu open={open} onOpenChange={(e, data) => setOpen(data.open)}>
      <MenuTrigger disableButtonEnhancement>
        <Button
          appearance="subtle"
          icon={<Navigation24Regular />}
          aria-label="Menu"
        />
      </MenuTrigger>

      <MenuPopover>
        <MenuList>
          <MenuItem onClick={() => handleItemClick("hourly_agenda")}>
            Today&apos;s Schedule
          </MenuItem>
          <MenuItem onClick={() => handleItemClick("organizer_tools")}>
            Admin Tools
          </MenuItem>
        </MenuList>
      </MenuPopover>
    </Menu>
  );
};

export default HamburgerMenu;
