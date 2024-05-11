import { Card, Col, Empty, Row, Skeleton, Table, Typography } from "antd";

const Resource = ({ name, parameters }) => {
    return (
        <Card size="small" title={name}>
            <Table
                style={{ height: 200, overflowY: "scroll" }}
                size="small"
                columns={[
                    {
                        dataIndex: "parameter",
                        title: "Параметр",
                        render: (text) => (
                            <div
                                style={{
                                    whiteSpace: "nowrap",
                                    width: "8vw",
                                    overflowX: "hidden",
                                    textOverflow: "ellipsis",
                                }}
                                title={text}
                            >
                                {text}
                            </div>
                        ),
                    },
                    { dataIndex: "value", title: "Значение", render: (text) => (
                        <div
                            style={{
                                whiteSpace: "nowrap",
                                width: "6vw",
                                overflowX: "hidden",
                                textOverflow: "ellipsis",
                            }}
                            title={text}
                        >
                            {text}
                        </div>
                    ),},
                ]}
                dataSource={Object.entries(parameters).map(([key, value]) => ({ parameter: key, value }))}
                pagination={false}
            />
        </Card>
    );
};

const ATSimulation = ({ atSimulation, inferenceNow }) => {
    return !atSimulation ? (
        !inferenceNow ? (
            <Empty description="Ожидание начала совместного функционирования" />
        ) : (
            <Skeleton active />
        )
    ) : (
        <>
            <Typography.Title level={3}>Параметры ресурсов</Typography.Title>
            <Row gutter={[10, 10]}>
                {atSimulation.map((resource) => (
                    <Col span={8}>
                        <Resource key={resource.name} {...resource} />
                    </Col>
                ))}
            </Row>
        </>
    );
};

export default ATSimulation;
