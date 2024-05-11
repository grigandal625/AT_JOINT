import { LogoutOutlined, PlayCircleOutlined } from "@ant-design/icons";
import { Form, InputNumber, Button, Space } from "antd";

const StartInference = ({ token, inferenceNow, setInferenceNow, exit }) => {
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

    return (
        <Form disabled={inferenceNow} initialValues={{ iterate: 1, wait: 500 }} onFinish={onFinish} layout="inline">
            <Form.Item name="iterate" label="Количество тактов">
                <InputNumber min={1} step={1} />
            </Form.Item>
            <Form.Item name="wait" label="Ожидание между тактами (миллисикунд)">
                <InputNumber min={0} step={1} />
            </Form.Item>
            <Space>
                <Form.Item>
                    <Button icon={<PlayCircleOutlined />} type="primary" htmlType="submit">
                        Запустить темпоральный вывод
                    </Button>
                </Form.Item>
                <Button icon={<LogoutOutlined />} onClick={exit}>
                    Отключиться
                </Button>
            </Space>
        </Form>
    );
};

export default StartInference;
