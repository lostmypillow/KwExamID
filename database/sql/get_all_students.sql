-- SELECT
--     A.身分證,
--     A.學號,
--     A.姓名,
--     A.生日
-- FROM
--     學生資料 AS A
--     LEFT JOIN [學生大考資料] AS B ON A.[學號] = B.[學號]
--     AND B.年度 = (YEAR(GETDATE()) - 1911)
-- WHERE
--     A.學號 IN (
--         SELECT
--             DISTINCT 學號
--         FROM
--             學生欠費
--         WHERE
--             (
--                 班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1912) AS VARCHAR) + '%高三數學班%'
--                 -- OR 班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1913) AS VARCHAR) + '%高二數學班%'
--                 -- OR 班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1914) AS VARCHAR) + '%高一數學班%'
--             )
--     )
--     AND isnull(B.學測准考證, '') = ''
--     AND (
--         B.[狀態] NOT LIKE (CONVERT(VARCHAR, GETDATE(), 112) + '資料錯誤%')
--         OR B.[狀態] IS NULL
--     )
--     AND 身分證 <> ''
-- ORDER BY
--     A.學號;

SELECT
    A.身分證,
    A.學號,
    A.姓名,
    A.生日
FROM
    學生資料 AS A
    LEFT JOIN [學生大考資料] AS B ON A.[學號] = B.[學號]
    AND B.年度 = (YEAR(GETDATE()) - 1911)
WHERE
    A.學號 IN (
        SELECT
            DISTINCT 學號
        FROM
            學生欠費
        WHERE
            (
                班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1912) AS VARCHAR) + '%高三數學班%'
                OR 班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1913) AS VARCHAR) + '%高二數學班%'
                OR 班級名稱 LIKE '%' + CAST((YEAR(GETDATE()) - 1914) AS VARCHAR) + '%高一數學班%'
            )
    )
    AND 身分證 <> ''
ORDER BY
    A.學號;