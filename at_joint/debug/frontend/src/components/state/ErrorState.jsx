import { Tag, Table, Row, Col, Space, Button, Typography } from "antd";
import {
    CheckCircleOutlined,
    CloseCircleOutlined,
    LoginOutlined,
    QuestionCircleOutlined,
    RetweetOutlined,
} from "@ant-design/icons";
import { useNavigate } from "react-router-dom";

const components = {
    at_joint: "Компонент поддержки совместного функционирования",
    at_solver: "АТ-РЕШАТЕЛЬ",
    at_temporal_solver: "Темпоральный решатель",
    at_simulation: "Подсистема имитационного моделирования",
    at_blackboard: "Динамическая классная доска",
};

const ErrorState = ({ token, componentsState, loadComponentState, setComponentState }) => {
    const navigate = useNavigate();
    return (
        <div>
            <Row wrap={false}>
                <Col flex="auto">
                    <Typography.Title level={4}>Ошибка</Typography.Title>
                </Col>
                <Col>
                    <Space>
                        <Button
                            icon={<RetweetOutlined />}
                            type="primary"
                            onClick={() => {
                                setComponentState(null);
                                loadComponentState(token, setComponentState);
                            }}
                        >
                            Проверить компоненты повторно
                        </Button>
                        <Button
                            icon={<LoginOutlined />}
                            onClick={() => {
                                localStorage.removeItem("token");
                                navigate("/token");
                            }}
                        >
                            Ввести другой ключ доступа
                        </Button>
                    </Space>
                </Col>
            </Row>
            <Row>
                <Table
                    dataSource={Object.entries(componentsState).map(([key, value]) => ({ component: key, ...value }))}
                    columns={[
                        { title: "Компонент", render: (data) => components[data.component] },
                        {
                            title: "Статус регистрации",
                            dataIndex: "registered",
                            render: (data) =>
                                data.hasOwnProperty("registered") ? (
                                    data.registered ? (
                                        <Tag icon={<CheckCircleOutlined />} color="green">
                                            Зарегистрирован
                                        </Tag>
                                    ) : (
                                        <Tag icon={<CloseCircleOutlined />} color="red">
                                            Не зарегистрирован
                                        </Tag>
                                    )
                                ) : (
                                    <Tag icon={<QuestionCircleOutlined />} color="yellow">
                                        Ожидается регистрация и конфигурация компонента поддержки совместного
                                        функционирования
                                    </Tag>
                                ),
                        },
                        {
                            title: "Статус конфигурации",
                            dataIndex: "configured",
                            render: (data) =>
                                data.hasOwnProperty("configured") ? (
                                    data.configured ? (
                                        <Tag icon={<CheckCircleOutlined />} color="green">
                                            Конфигурация применена
                                        </Tag>
                                    ) : (
                                        <Tag icon={<CloseCircleOutlined />} color="red">
                                            Конфигурация не применена
                                        </Tag>
                                    )
                                ) : (
                                    <Tag icon={<QuestionCircleOutlined />} color="yellow">
                                        Ожидается регистрация и конфигурация компонента поддержки совместного
                                        функционирования
                                    </Tag>
                                ),
                        },
                    ]}
                />
            </Row>
        </div>
    );
};

export default ErrorState;
