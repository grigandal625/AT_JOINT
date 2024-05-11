import { Form, Input, Button } from "antd";
import { useNavigate } from "react-router-dom";

export default () => {
    const token = localStorage.getItem("token");
    const navigate = useNavigate();
    if (token) {
        navigate(`/state?token=${token}`);
    }
    const onFinish = (values) => {
        localStorage.setItem("token", values.token);
        navigate(`/state?token=${values.token}`);
    };
    return (
        <Form name="basic" onFinish={onFinish} layout="inline">
            <Form.Item
                label="Ключ доступа"
                name="token"
                rules={[
                    {
                        required: true,
                        message: "Введите ключ!",
                    },
                ]}
            >
                <Input />
            </Form.Item>
            <Form.Item>
                <Button type="primary" htmlType="submit">
                    Подключиться
                </Button>
            </Form.Item>
        </Form>
    );
};
