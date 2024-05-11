import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { message, Row, Col, Divider, Form, Checkbox, Collapse, Card } from "antd";
import StartInference from "./start_inference/StartInference";
import ATSimulation from "./panels/ATSimulation";
import ATSolver from "./panels/ATSolver";
import ATTemporalSolver from "./panels/ATTemporalSolver";

const CheckboxField = ({ value, onChange }) => (
    <Checkbox checked={value} onChange={(e) => onChange(e.target.checked)} />
);

const SettingsForm = ({ settings, setSettings }) => {
    const [form] = Form.useForm();
    return (
        <Form
            form={form}
            onValuesChange={() => form.submit()}
            initialValues={settings}
            onFinish={(values) => setSettings(values)}
            layout="inline"
        >
            <Form.Item name="atSimulation" label="Панель подсистемы ИМ">
                <CheckboxField />
            </Form.Item>
            <Form.Item name="atTemporalSolver" label="Панель темпорального решателя">
                <CheckboxField />
            </Form.Item>
            <Form.Item name="atSolver" label="Панель АТ-РЕШАТЕЛЯ">
                <CheckboxField />
            </Form.Item>
        </Form>
    );
};

const Connection = ({ token }) => {
    const [atSimulation, setAtSimulation] = useState();
    const [atTemporalSolver, setAtTemporalSolver] = useState();
    const [atSolver, setAtSolver] = useState();

    const [inferenceNow, setInferenceNow] = useState(false);

    const [settings, setSettings] = useState({
        atSimulation: true,
        atTemporalSolver: true,
        atSolver: true,
    });

    const navigate = useNavigate();
    const exit = () => {
        localStorage.removeItem("token");
        navigate("/token");
    };

    useEffect(() => {
        const url = process.env.REACT_APP_WS_URL || `ws://${window.location.host}`;
        const ws = new WebSocket(`${url}/api/ws?token=${token}`);
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
                            setInferenceNow(false);
                        }
                    default:
                        break;
                }
            } catch (error) {
                console.error(error);
            }
        };
    }, [token]);

    return (
        <div>
            <StartInference token={token} inferenceNow={inferenceNow} setInferenceNow={setInferenceNow} exit={exit} />
            <Divider />
            <Collapse
                items={[
                    {
                        key: "settings",
                        label: "Вид",
                        children: <SettingsForm settings={settings} setSettings={setSettings} />,
                    },
                ]}
            />
            <br />
            <Row gutter={[10, 10]}>
                {settings.atSimulation ? (
                    <Col>
                        <Card title="Подсистема имитационного моделирования">
                            <ATSimulation inferenceNow={inferenceNow} atSimulation={atSimulation?.data} />
                        </Card>
                    </Col>
                ) : (
                    <></>
                )}
                {settings.atTemporalSolver ? (
                    <Col>
                        <Card title="Темпоральный решатель">
                            <ATTemporalSolver
                                inferenceNow={inferenceNow}
                                atTemporalSolver={atTemporalSolver?.data}
                            />
                        </Card>
                    </Col>
                ) : (
                    <></>
                )}
                {settings.atSolver ? (
                    <Col>
                        <Card title="АТ-РЕШАТЕЛЬ">
                            <ATSolver inferenceNow={inferenceNow} atSolver={atSolver?.data} />
                        </Card>
                    </Col>
                ) : (
                    <></>
                )}
            </Row>
        </div>
    );
};

export default Connection;
