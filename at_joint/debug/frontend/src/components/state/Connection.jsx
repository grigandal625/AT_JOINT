import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { message, Row, Col, Divider, Button, Tabs } from "antd";
import StartInference from "./start_inference/StartInference";
import ATSimulation from "./panels/ATSimulation";
import ATSolver from "./panels/ATSolver";
import ATTemporalSolver from "./panels/ATTemporalSolver";
import { RollbackOutlined, StopOutlined } from "@ant-design/icons";

const Connection = ({ token }) => {
    const [atSimulation, setAtSimulation] = useState();
    const [atTemporalSolver, setAtTemporalSolver] = useState();
    const [atSolver, setAtSolver] = useState();

    const [inferenceNow, setInferenceNow] = useState(false);

    const navigate = useNavigate();
    const exit = () => {
        localStorage.removeItem("token");
        navigate("/token");
    };

    useEffect(() => {
        const url = process.env.REACT_APP_WS_URL || `ws://${window.location.host}`;
        const ws = new WebSocket(`${url}/api/ws?auth_token=${token}`);
        ws.onclose = () => {
            message.error("Соединение с сервером разорвано");
            localStorage.removeItem("token");
            navigate("/token");
        };
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                switch (data?.initiator) {
                    case "at_simulation":
                        setAtSimulation(data);
                        setInferenceNow(true);
                        break;
                    case "at_temporal_solver":
                        setAtTemporalSolver(data);
                        setInferenceNow(true);
                        break;
                    case "at_solver":
                        setAtSolver(data);
                        setInferenceNow(true);
                        break;
                    case "at_joint":
                        if (data?.data?.stop) {
                            message.info("Совместное функционирование остановлено");
                            setInferenceNow(false);
                            setIsStopping(false);
                        }
                    default:
                        break;
                }
            } catch (error) {
                console.error(error);
            }
        };
    }, [token]);

    const [isStopping, setIsStopping] = useState(false);

    const stopInference = async () => {
        const url = process.env.REACT_APP_API_URL || "";
        setIsStopping(true);
        const response = await fetch(`${url}/api/stop?token=${token}`);
        if (response.status === 200) {
            message.success("Отсановка совместного функционирования запущена, ожидайте.");
        } else {
            message.error("Ошибка при остановке");
            setIsStopping(false);
        }
    };

    const reset = async () => {
        const url = process.env.REACT_APP_API_URL || "";
        const response = await fetch(`${url}/api/reset?token=${token}`);
        if (response.status === 200) {
            message.success("Сброс выполнен");
            setAtSimulation(null);
            setAtTemporalSolver(null);
            setAtSolver(null);
        } else {
            message.error("Ошибка при сбросе");
        }
    };

    const tabItems = [];

    return (
        <div>
            <Row gutter={[10, 10]}>
                <StartInference asRow={false} token={token} inferenceNow={inferenceNow} setInferenceNow={setInferenceNow} exit={exit} />
                <Col>
                    <Button
                        disabled={inferenceNow ? isStopping : false}
                        danger
                        icon={inferenceNow ? <StopOutlined /> : <RollbackOutlined />}
                        onClick={inferenceNow ? stopInference : reset}
                    >
                        {inferenceNow ? "Стоп" : "Сброс"}
                    </Button>
                </Col>
            </Row>
            <Divider />
            <Tabs
                items={[
                    {
                        key: 'at_simulation_subsystem',
                        label: "Подсистема имитационного моделирования",
                        children: <ATSimulation inferenceNow={inferenceNow} atSimulation={atSimulation?.data} />,
                    },
                    {
                        key: 'at_temporal_solver',
                        label: "Темпоральный решатель",
                        children: <ATTemporalSolver inferenceNow={inferenceNow} atTemporalSolver={atTemporalSolver?.data} />,
                    },
                    {
                        key: 'at_solver',
                        label: "АТ-РЕШАТЕЛЬ",
                        children: <ATSolver inferenceNow={inferenceNow} atSolver={atSolver?.data} />,
                    },
                ]}
            />
        </div>
    );
};

export default Connection;
