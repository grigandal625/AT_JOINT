import { Tabs, Layout } from "antd";
import PageHeader from "./utils/PageHeader";
import ThemedContainer from "./utils/ThemedContainer";
import {
    Outlet,
    Route,
    RouterProvider,
    createBrowserRouter,
    createRoutesFromElements,
    useNavigate,
} from "react-router-dom";
import Token from "./components/Token";
import State from "./components/State";
import { useEffect } from "react";

const AppLayout = () => {
    const navigate = useNavigate();
    useEffect(() => {
        if (window.location.origin == window.location.href || window.location.origin + "/" == window.location.href) {
            navigate("/token");
        }
    }, []);
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
            <Route index path="token" element={<Token />} />
            <Route path="state" element={<State />} />
        </Route>
    )
);

export default () => <RouterProvider router={router} />;
