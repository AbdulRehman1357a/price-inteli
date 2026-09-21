import Container from "@mui/material/Container";
import Paper from "@mui/material/Paper";
import Typography from "@mui/material/Typography";
import { useNavigate } from "react-router-dom";

import UserForm from "../features/users/UserForm";
import { useCreateUser } from "../features/users/hooks";

export default function UserCreatePage() {
  const navigate = useNavigate();
  const createUser = useCreateUser();

  const handleSubmit = async (values) => {
    await createUser.mutateAsync(values);
    navigate("/users", { replace: true });
  };

  return (
    <Container maxWidth="md" sx={{ py: 4 }}>
      <Typography variant="h4" component="h1" gutterBottom>
        New User
      </Typography>
      <Paper variant="outlined" sx={{ p: 3, mt: 2 }}>
        <UserForm mode="create" onSubmit={handleSubmit} submitLabel="Create User" />
      </Paper>
    </Container>
  );
}
