import AccountCircle from "@mui/icons-material/AccountCircle";
import Divider from "@mui/material/Divider";
import IconButton from "@mui/material/IconButton";
import ListItemText from "@mui/material/ListItemText";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import { useAuth } from "../features/auth/AuthContext";

export default function ProfileMenu() {
  const { user, organization, logout, hasPermission } = useAuth();
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  const handleLogout = async () => {
    setAnchorEl(null);
    await logout();
    navigate("/login", { replace: true });
  };

  const handleProfile = () => {
    setAnchorEl(null);
    navigate("/profile");
  };

  const handleStores = () => {
    setAnchorEl(null);
    navigate("/stores");
  };

  const handleSettings = () => {
    setAnchorEl(null);
    navigate("/settings");
  };

  const handleNavigate = (to) => {
    setAnchorEl(null);
    navigate(to);
  };

  return (
    <>
      <IconButton
        onClick={(event) => setAnchorEl(event.currentTarget)}
        size="large"
        color="inherit"
        aria-label="account menu"
        aria-controls={open ? "profile-menu" : undefined}
        aria-haspopup="true"
      >
        <AccountCircle />
      </IconButton>
      <Menu
        id="profile-menu"
        anchorEl={anchorEl}
        open={open}
        onClose={() => setAnchorEl(null)}
        anchorOrigin={{ vertical: "bottom", horizontal: "right" }}
        transformOrigin={{ vertical: "top", horizontal: "right" }}
      >
        <MenuItem disabled divider sx={{ opacity: "1 !important" }}>
          <ListItemText
            primary={`${user?.first_name ?? ""} ${user?.last_name ?? ""}`.trim()}
            secondary={organization?.name}
          />
        </MenuItem>
        <Divider />
        <MenuItem onClick={handleProfile}>Profile</MenuItem>
        <MenuItem onClick={handleStores} sx={{ pl: 4 }}>
          Stores
        </MenuItem>
        <Divider />
        {hasPermission("pricing.read") && (
          <MenuItem onClick={() => handleNavigate("/pricing/simulate")}>Simulation</MenuItem>
        )}
        {hasPermission("pricing.read") && (
          <MenuItem onClick={() => handleNavigate("/competitors/dashboard")}>Competitors</MenuItem>
        )}
        {hasPermission("ai_recommendations.read") && (
          <MenuItem onClick={() => handleNavigate("/ai-pricing")}>AI Pricing</MenuItem>
        )}
        {hasPermission("ai_recommendations.read") && (
          <MenuItem onClick={() => handleNavigate("/ai-agents")}>AI Agents</MenuItem>
        )}
        <Divider />
        <MenuItem onClick={handleSettings}>Settings</MenuItem>
        <Divider />
        <MenuItem onClick={handleLogout}>Log out</MenuItem>
      </Menu>
    </>
  );
}
