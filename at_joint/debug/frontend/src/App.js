import { Tabs, Layout } from "antd";
import PageHeader from "./utils/PageHeader";
import ThemedContainer from "./utils/ThemedContainer";
import { Outlet, Route, RouterProvider, createBrowserRouter, createRoutesFromElements } from "react-router-dom";
import Token from "./components/Token";
import State from "./components/State";

const AppLayout = () => {
    return (
        <Layout>
            <Layout.Header>
                <PageHeader style={{ color: "white" }} title="Компонент отладки совместного функционирования" />
            </Layout.Header>
            <Layout.Content>
                <ThemedContainer>
                    <Outlet />
                </ThemedContainer>
            </Layout.Content>
            <Layout.Footer>Лаборатория «Интеллекутальные системы и технологии» ©2024</Layout.Footer>
        </Layout>
    );
};

export const router = createBrowserRouter(
    createRoutesFromElements(
        <Route path="" element={<AppLayout />}>
            <Route path="token" element={<Token />} />
            <Route path="state" element={<State />} />
        </Route>
    )
);

export default () => <RouterProvider router={router} />;
