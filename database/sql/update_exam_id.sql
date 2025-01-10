MERGE INTO [學生大考資料] AS target USING (
    SELECT
        :student_id AS student_id,
        :exam_id AS exam_id,
        :status_msg AS status_msg
) AS source ON target.[學號] = source.[student_id]
AND target.年度 = (YEAR(GETDATE()) - 1911)
WHEN MATCHED THEN
UPDATE
SET
    target.學測准考證 = source.exam_id,
    target.更新日期 = SYSDATETIME(),
    target.狀態 = source.status_msg
    WHEN NOT MATCHED BY TARGET THEN
INSERT
    (年度, 學號, 學測准考證, 更新日期, 狀態)
VALUES
    (
        (YEAR(GETDATE()) - 1911),
        source.student_id,
        source.exam_id,
        SYSDATETIME(),
        source.status_msg
    );

-- no CONVERT(VARCHAR, GETDATE(), 112) here because we might need to insert the error version of that , namely CONVERT(VARCHAR, GETDATE(), 112) + "資料錯誤"