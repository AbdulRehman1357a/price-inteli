import ArrowDropDownIcon from "@mui/icons-material/ArrowDropDown";
import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import MenuIcon from "@mui/icons-material/Menu";
import AppBar from "@mui/material/AppBar";
import Box from "@mui/material/Box";
import Button from "@mui/material/Button";
import Collapse from "@mui/material/Collapse";
import Divider from "@mui/material/Divider";
import Drawer from "@mui/material/Drawer";
import IconButton from "@mui/material/IconButton";
import List from "@mui/material/List";
import ListItemButton from "@mui/material/ListItemButton";
import ListItemText from "@mui/material/ListItemText";
import Menu from "@mui/material/Menu";
import MenuItem from "@mui/material/MenuItem";
import Stack from "@mui/material/Stack";
import { useTheme } from "@mui/material/styles";
import Toolbar from "@mui/material/Toolbar";
import Typography from "@mui/material/Typography";
import useMediaQuery from "@mui/material/useMediaQuery";
import { useEffect, useState } from "react";
import { Link as RouterLink, Outlet, useLocation, useNavigate } from "react-router-dom";

import Logo from "../components/Logo";
import ProfileMenu from "../components/ProfileMenu";
import { useAuth } from "../features/auth/AuthContext";

// A header button that opens a dropdown of related links — used for
// "Pricing Rules" (-> Simulation, Competitors) and "AI Agents" (-> AI
// Pricing), so those two pages stay reachable without every related page
// needing its own top-level header button. Desktop (>= md) only — see
// NavDrawerGroup for the < md equivalent.
function NavMenuButton({ label, items }) {
  const navigate = useNavigate();
  const [anchorEl, setAnchorEl] = useState(null);
  const open = Boolean(anchorEl);

  if (items.length === 0) return null;

  const handleSelect = (to) => {
    setAnchorEl(null);
    navigate(to);
  };

  return (
    <>
      <Button
        color="inherit"
        onClick={(event) => setAnchorEl(event.currentTarget)}
        endIcon={<ArrowDropDownIcon />}
        aria-haspopup="true"
        aria-expanded={open ? "true" : undefined}
      >
        {label}
      </Button>
      <Menu anchorEl={anchorEl} open={open} onClose={() => setAnchorEl(null)}>
        {items.map((item) => (
          <MenuItem key={item.to} onClick={() => handleSelect(item.to)}>
            {item.label}
          </MenuItem>
        ))}
      </Menu>
    </>
  );
}

// The < md equivalent of NavMenuButton: a popover Menu is the wrong idiom
// inside a vertical Drawer list, so this expands/collapses its sub-items
// in place instead — same {label, items} shape, same permission-gated
// arrays, only the rendering differs by breakpoint.
function NavDrawerGroup({ label, items, onNavigate }) {
  const [open, setOpen] = useState(false);

  if (items.length === 0) return null;

  return (
    <>
      <ListItemButton onClick={() => setOpen((prev) => !prev)}>
        <ListItemText primary={label} />
        {open ? <ExpandLessIcon /> : <ExpandMoreIcon />}
      </ListItemButton>
      <Collapse in={open} timeout="auto" unmountOnExit>
        <List component="div" disablePadding>
          {items.map((item) => (
            <ListItemButton
              key={item.to}
              component={RouterLink}
              to={item.to}
              onClick={onNavigate}
              sx={{ pl: 4 }}
            >
              <ListItemText primary={item.label} />
            </ListItemButton>
          ))}
        </List>
      </Collapse>
    </>
  );
}

const PRIMARY_NAV_ITEMS = [
  { to: "/dashboard", label: "Dashboard" },
  { to: "/categories", label: "Categories" },
  { to: "/products", label: "Products" },
  { to: "/inventory", label: "Inventory" },
];

export default function MainLayout() {
  const { isAuthenticated, hasPermission } = useAuth();
  const theme = useTheme();
  const isNavCollapsed = useMediaQuery(theme.breakpoints.down("md"));
  const [drawerOpen, setDrawerOpen] = useState(false);
  const location = useLocation();

  const pricingMenuItems = [
    { to: "/pricing/rules", label: "Pricing Rules" },
    ...(hasPermission("pricing.read")
      ? [
          { to: "/pricing/simulate", label: "Simulation" },
          { to: "/competitors/dashboard", label: "Competitors" },
        ]
      : []),
  ];

  const aiMenuItems = [
    { to: "/ai-agents", label: "AI Agents" },
    ...(hasPermission("ai_recommendations.read") ? [{ to: "/ai-pricing", label: "AI Pricing" }] : []),
  ];

  // Tapping a Drawer link navigates via RouterLink, but the Drawer's own
  // open state needs closing too — a route change is the reliable signal.
  useEffect(() => {
    setDrawerOpen(false);
  }, [location.pathname]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", minHeight: "100vh" }}>
      <AppBar position="static">
        <Toolbar>
          {isAuthenticated && isNavCollapsed && (
            <IconButton
              color="inherit"
              edge="start"
              aria-label="open navigation menu"
              onClick={() => setDrawerOpen(true)}
              sx={{ mr: 1 }}
            >
              <MenuIcon />
            </IconButton>
          )}
          <Stack
            direction="row"
            alignItems="center"
            spacing={1.5}
            component={RouterLink}
            to={isAuthenticated ? "/dashboard" : "/"}
            sx={{ flexGrow: 1, textDecoration: "none", color: "inherit", minWidth: 0 }}
          >
            <Logo size={32} />
            <Typography
              variant="h6"
              noWrap
              component="span"
              sx={{ display: { xs: "none", sm: "block" } }}
            >
              Pricing Intelligent Platform
            </Typography>
            <Typography
              variant="h6"
              noWrap
              component="span"
              sx={{ display: { xs: "block", sm: "none" } }}
            >
              PIP
            </Typography>
          </Stack>
          {isAuthenticated && !isNavCollapsed && (
            <Stack direction="row" spacing={1} alignItems="center" sx={{ mr: 2 }}>
              <Button color="inherit" component={RouterLink} to="/dashboard">
                Dashboard
              </Button>
              <Button color="inherit" component={RouterLink} to="/categories">
                Categories
              </Button>
              <Button color="inherit" component={RouterLink} to="/products">
                Products
              </Button>
              <Button color="inherit" component={RouterLink} to="/inventory">
                Inventory
              </Button>
              <NavMenuButton label="Pricing Rules" items={pricingMenuItems} />
              {hasPermission("ai_recommendations.read") && (
                <NavMenuButton label="AI Agents" items={aiMenuItems} />
              )}
            </Stack>
          )}
          {isAuthenticated ? (
            <ProfileMenu />
          ) : (
            <Button color="inherit" component={RouterLink} to="/login">
              Sign in
            </Button>
          )}
        </Toolbar>
      </AppBar>

      {isAuthenticated && (
        <Drawer anchor="left" open={drawerOpen} onClose={() => setDrawerOpen(false)}>
          <Box sx={{ width: 260 }} role="presentation">
            <List>
              {PRIMARY_NAV_ITEMS.map((item) => (
                <ListItemButton key={item.to} component={RouterLink} to={item.to}>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              ))}
            </List>
            <Divider />
            <List>
              <NavDrawerGroup
                label="Pricing Rules"
                items={pricingMenuItems}
                onNavigate={() => setDrawerOpen(false)}
              />
              {hasPermission("ai_recommendations.read") && (
                <NavDrawerGroup
                  label="AI Agents"
                  items={aiMenuItems}
                  onNavigate={() => setDrawerOpen(false)}
                />
              )}
            </List>
          </Box>
        </Drawer>
      )}

      <Box component="main" sx={{ flex: 1 }}>
        <Outlet />
      </Box>
    </Box>
  );
}
