import { LogoutOutlined, PlayCircleOutlined } from "@ant-design/icons";
import { Form, InputNumber, Button, Row, Col } from "antd";

const StartInference = ({ token, inferenceNow, setInferenceNow, exit, asRow, gutter }) => {
    const onFinish = async (values) => {
        const url = process.env.REACT_APP_API_URL || "";
        const response = await fetch(`${url}/api/process_tact?token=${token}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify(values),
        });
        const data = await response.json();
        if (data.success) {
            setInferenceNow(true);
        }
    };

    const mainForm = (
        <Form disabled={inferenceNow} initialValues={{ iterate: 1, wait: 500 }} onFinish={onFinish} layout="inline">
            <Col>
                <Form.Item name="iterate" label="Количество тактов">
                    <InputNumber min={1} step={1} />
                </Form.Item>
            </Col>
            <Col>
                <Form.Item name="wait" label="Ожидание между тактами (миллисикунд)">
                    <InputNumber min={0} step={1} />
                </Form.Item>
            </Col>
            <Col>
                <Form.Item>
                    <Button icon={<PlayCircleOutlined />} type="primary" htmlType="submit">
                        Запустить темпоральный вывод
                    </Button>
                </Form.Item>
            </Col>
            <Col>
                <Button icon={<LogoutOutlined />} onClick={exit}>
                    Отключиться
                </Button>
            </Col>
        </Form>
    );

    return asRow ? <Row gutter={gutter || [10, 10]}>{mainForm}</Row> : mainForm;
};

export default StartInference;
