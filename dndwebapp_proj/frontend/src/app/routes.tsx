import { createBrowserRouter } from "react-router";
import { Root } from "./Root";
import { Home } from "./pages/Home";
import { HandbookPage } from "./pages/HandbookPage";
import { GlossaryPage } from "./pages/GlossaryPage";
import { CreateCharacterPage } from "./pages/CreateCharacterPage";
import { MyWorksPage } from "./pages/MyWorksPage";
import { ProfilePage } from "./pages/ProfilePage";
import { ChatHistoryPage } from "./pages/ChatHistoryPage";
import { AdminPage } from "./pages/AdminPage";
import { ToolsPage } from "./pages/ToolsPage";

export const router = createBrowserRouter([
  {
    path: "/",
    Component: Root,
    children: [
      { index: true, Component: Home },
      { path: "handbook", Component: HandbookPage },
      { path: "glossary", Component: GlossaryPage },
      { path: "create-character", Component: CreateCharacterPage },
      { path: "my-works", Component: MyWorksPage },
      { path: "profile", Component: ProfilePage },
      { path: "chat-history", Component: ChatHistoryPage },
      { path: "admin", Component: AdminPage },
      { path: "tools", Component: ToolsPage },
    ],
  },
]);