import { useSearchParams, useNavigate } from "react-router-dom";
import { Skeleton } from "antd";
import { useEffect, useState } from "react";
import ErrorState from "./state/ErrorState";
import Connection from "./state/Connection";

const loadComponentState = async (token, setComponentsState) => {
    const url = process.env.REACT_APP_API_URL || "";
    const response = await fetch(`${url}/api/state?token=${token}`);
    const componentsState = await response.json();
    setComponentsState(componentsState);
};

const State = () => {
    const navigate = useNavigate();
    const [searchParams, _] = useSearchParams();
    const token = searchParams.get("token");
    if (!token) {
        navigate("/token");
    }
    localStorage.setItem("token", token);

    const [componentsState, setComponentsState] = useState(null);

    useEffect(() => {
        loadComponentState(token, setComponentsState);
    }, [token]);

    let error = null;
    if (componentsState) {
        for (let component in componentsState) {
            component = componentsState[component];
            if (!component.registered || !component.configured) {
                error = true;
                break;
            }
        }
    }

    return !componentsState ? (
        <Skeleton active />
    ) : error ? (
        <ErrorState token={token} componentsState={componentsState} loadComponentState={loadComponentState} setComponentsState={setComponentsState} />
    ) : (
        <Connection token={token} />
    );
};

export default State;
