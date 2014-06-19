# 1. 회원 가입

DROP PROCEDURE IF EXISTS sp_enterance;
DELIMITER $$
CREATE PROCEDURE sp_enterance(	IN input_id VARCHAR(20), 
								IN input_name VARCHAR(40), 
								IN input_passwd VARCHAR(40), 
								OUT output_result INT	)
BEGIN
	START TRANSACTION;
	SET output_result = NULL;

	SELECT user_id INTO output_result FROM user u
		WHERE u.login_id = input_id;

	IF output_result is NULL
		THEN SET output_result = 0;
		INSERT INTO user (login_id, name, passwd, level)
			VALUES (input_id, input_name, MD5(input_passwd), 'member');
		COMMIT;
	ELSE
		ROLLBACK;
	END IF;

	SELECT output_result;

END $$
DELIMITER ;

# 사용법
SET @result = 0;
CALL sp_enterance('아이디', '유저명', '패스워드', @result);

SELECT @result;
# -> 0이면 입력 성공 or 실패


# 2. 로그인

DROP PROCEDURE IF EXISTS sp_login;
DELIMITER $$
CREATE PROCEDURE sp_login(	IN input_id VARCHAR(20),  
							IN input_passwd VARCHAR(40), 
							OUT output_result INT	)
BEGIN
	DECLARE user_level VARCHAR(20);
	DECLARE passwd_result VARCHAR(40);
	DECLARE user_name VARCHAR(40);

	START TRANSACTION;

	SET output_result = NULL;
	SELECT user_id INTO output_result FROM user u
		WHERE u.login_id = input_id limit 1;

	IF output_result is NULL
		THEN SET output_result = 0;
		INSERT INTO log ( log_result )
			VALUES ( CONCAT(input_id, '# ID not found') );

	ELSE
		SELECT name, passwd, level INTO user_name, passwd_result, user_level FROM user u
			WHERE u.user_id = output_result;

		IF passwd_result <> MD5(input_passwd)
			THEN SET output_result = -1;
			INSERT INTO log ( log_result )
				VALUES ( CONCAT(input_id, '# Password Error ') );
		ELSEIF user_level = 'blocked'
			THEN
			INSERT INTO log ( log_result )
				VALUES ( CONCAT(input_id, '# Login Blocked User') );
			SET output_result = -2;

		ELSE
			INSERT INTO log ( log_result )
				VALUES ( CONCAT(input_id, '# Login Success') );
		END IF;
	END IF;

	COMMIT;

	SELECT output_result, user_name, user_level;
END $$
DELIMITER ;

# 사용법
SET @result = NULL;
CALL sp_login('아이디', '패스워드', @result);

SELECT @result;
# -> 0이면 없는 아이디 or -1이면 잘못 된 패스워드 or -2이면 블록 유저 or 정상 로그인 시 받아온 유저인덱스


# 3. 문서 작성

DROP PROCEDURE IF EXISTS sp_write;
DELIMITER $$
CREATE PROCEDURE sp_write(	IN input_id INT,
							IN input_title VARCHAR(80),
							IN input_contents BLOB,
							IN input_category VARCHAR(40)	)
BEGIN
	DECLARE c_index INT;
	DECLARE d_index INT;

	START TRANSACTION;

	SET d_index = NULL;
	SELECT document_id INTO d_index FROM document
		WHERE title = input_title;

	IF d_index is NULL
		THEN
		SELECT category_id INTO c_index FROM category
			WHERE category_name = input_category;

		INSERT INTO document (title, user_id, last_history, editable, category_id)
			VALUES (input_title, input_id, 1, 0, c_index);

		UPDATE category c
			SET count = count + 1 WHERE c.category_id = c_index;

		SELECT document_id INTO d_index FROM document
			WHERE title = input_title;

		INSERT INTO history (document_id, document_index, user_id, contents)
			VALUES (d_index, 1, input_id, input_contents);

		COMMIT;
	ELSE
		ROLLBACK;
	END IF;

END $$
DELIMITER ;

# 사용법
CALL sp_write(유저인덱스, '글제목', '컨텐츠', '카테고리');

# 참고 1. 로그인 결과 받아온 유저 인덱스를 세션 저장 한 후 여기에 입력
# 참고 2. 문서 편집 시 카테고리 리스트를 얻어온 후에 가능한 카테고리를 입력한다.


# 4. 문서 조회

DROP PROCEDURE IF EXISTS sp_read;
DELIMITER $$
CREATE PROCEDURE sp_read(	IN input_title VARCHAR(80),
							OUT output_result INT	)
BEGIN
	DECLARE h_index INT;
	DECLARE editable_code INT;
	
	START TRANSACTION;

	SELECT document_id, last_history, editable INTO output_result, h_index, editable_code
		FROM document
		WHERE title = input_title;

	IF output_result is NULL
		THEN SET output_result = 0;
		SELECT output_result;
	ELSE
		IF editable_code <> 0
			THEN SET output_result = -output_result;
			SELECT output_result, CONVERT(contents USING utf8) as contents FROM history h
				WHERE h.document_id = (-output_result) AND h.document_index = h_index;
		ELSE
			SELECT output_result, CONVERT(contents USING utf8) as contents FROM history h
				WHERE h.document_id = output_result AND h.document_index = h_index;
		END IF;

	END IF;
	ROLLBACK;

END $$
DELIMITER ;

# 사용법
SET @result = NULL;
CALL sp_read('글제목', @result);

SELECT @result;
# -> 0이면 문서를 찾을 수 없다. -> 문서 작성 페이지로
# -> 0이 아니면 SELECT 결과로 컨텐츠가 나옴
# -> 음수면 수정 불가 문서


# 5. 문서 수정

DROP PROCEDURE IF EXISTS sp_update;
DELIMITER $$
CREATE PROCEDURE sp_update(	IN input_id INT,
							IN input_title VARCHAR(80),
							IN input_contents BLOB	)
BEGIN
	DECLARE d_index INT;
	DECLARE h_index INT;
	DECLARE editable_code INT;

	START TRANSACTION;

	SET d_index = NULL;
	SELECT document_id INTO d_index FROM document
		WHERE title = input_title;

	IF d_index is NULL
		THEN
			ROLLBACK;
	ELSE
		SELECT document_id, last_history, editable INTO d_index, h_index, editable_code 
			FROM document
			WHERE title = input_title;

		IF editable_code = 0
			THEN
			UPDATE document d
				SET d.last_history = h_index + 1 WHERE d.document_id = d_index;

			INSERT INTO history (document_id, document_index, user_id, contents)
				VALUES (d_index, h_index + 1, input_id, input_contents);

			COMMIT;
		ELSE
			ROLLBACK;
		END IF;
	END IF;
END $$
DELIMITER ;

# 사용법
CALL sp_update(유저인덱스, '글제목', '컨텐츠');

# 글제목은 수정 불가능하도록 만들어야 함


# 6. 이력 조회

DROP PROCEDURE IF EXISTS sp_history;
DELIMITER $$
CREATE PROCEDURE sp_history(	IN input_index INT,
								IN input_title VARCHAR(80)	)
BEGIN
	DECLARE d_index INT;

	SET d_index = NULL;

	SELECT document_id INTO d_index FROM document
		WHERE title = input_title;

	IF d_index is NOT NULL
		THEN
		IF input_index = 0
			THEN SELECT document_index, name, CONVERT(contents USING utf8) as contents, written_time
					FROM history h
					INNER JOIN user u
					WHERE h.document_id = d_index AND u.user_id = h.user_id ORDER BY document_index DESC;
		ELSE
			SELECT document_index, name, CONVERT(contents USING utf8) as contents, written_time
				FROM history h
				INNER JOIN user u
				WHERE h.document_id = d_index AND u.user_id = h.user_id AND h.document_index = input_index;
		END IF;
	END IF;
END $$
DELIMITER ;

# 사용법
CALL sp_history(이력순서, '글제목');

# 이력 순서에 0일 경우 모든 이력 조회, 아닐 경우 해당 이력 정보 조회


# 7. 문서 잠금

DROP PROCEDURE IF EXISTS sp_lock;
DELIMITER $$
CREATE PROCEDURE sp_lock(	IN input_id INT,
							IN input_title VARCHAR(80),
							IN input_lock_code INT	)
BEGIN
	DECLARE u_level VARCHAR(20) ;
	DECLARE d_index INT;
	
	START TRANSACTION;

	SELECT level INTO u_level FROM user u
		WHERE u.user_id = input_id;

	IF u_level = 'admin'
		THEN
		SELECT document_id INTO d_index FROM document
			WHERE title = input_title;

		UPDATE document d
			SET d.editable = input_lock_code WHERE d.document_id = d_index;
		COMMIT;
	ELSE
		ROLLBACK;

	END IF;

END $$
DELIMITER ;

# 사용법
CALL sp_lock(유저인덱스, '글제목', 잠금코드);

# 잠금 코드 0 : 잠금 아님


# 8. 문서 삭제

DROP PROCEDURE IF EXISTS sp_delete;
DELIMITER $$
CREATE PROCEDURE sp_delete(	IN input_id INT,
							IN input_title VARCHAR(80)	)
BEGIN
	DECLARE u_level VARCHAR(20);
	DECLARE d_index INT;

	START TRANSACTION;

	SELECT level INTO u_level FROM user u
		WHERE u.user_id = input_id;

	IF u_level = 'admin'
		THEN 
		SELECT document_id INTO d_index FROM document
			WHERE title = input_title;

		SET FOREIGN_KEY_CHECKS = 0; -- to disable them
		
		DELETE FROM history
			WHERE document_id = d_index;

		DELETE FROM document
			WHERE document_id = d_index;

		SET FOREIGN_KEY_CHECKS = 1; -- to re-enable them

		INSERT INTO log ( log_result )
			VALUES ( CONCAT(input_id, CONCAT('# Delete Document ', input_title)) );

		COMMIT;
	ELSE
		ROLLBACK;

		INSERT INTO log ( log_result )
			VALUES ( CONCAT(input_id, CONCAT('# Try To Delete Document ', input_title)) );

	END IF;

END $$
DELIMITER ;

# 사용법
CALL sp_delete(유저인덱스, '글제목');


# 9. 사용자 블록

DROP PROCEDURE IF EXISTS sp_block;
DELIMITER $$
CREATE PROCEDURE sp_block(	IN input_id INT,
							IN input_login_id VARCHAR(20)	)
BEGIN
	DECLARE u_level VARCHAR(20) ;
	DECLARE target_id INT ;

	START TRANSACTION;
	
	SELECT level INTO u_level FROM user u
		WHERE u.user_id = input_id;

	SELECT user_id INTO target_id FROM user u
		WHERE u.login_id = input_login_id;

	IF u_level = 'admin' AND target_id is NOT NULL
		THEN UPDATE user u
			SET u.level = 'blocked' WHERE u.login_id = input_login_id;

		INSERT INTO log ( log_result )
			VALUES ( CONCAT(input_id, CONCAT(input_login_id, ' User Is Blocked')) );
		COMMIT;
	ELSE
		ROLLBACK;

		INSERT INTO log ( log_result )
			VALUES ( CONCAT(input_id, CONCAT(' Is Try To Block ', input_login_id)) );
	END IF;

END $$
DELIMITER ;

# 사용법
CALL sp_block(유저인덱스, '블록대상ID');



String addr = "jdbc:mysql://10.73.45.50/mydb";
String user = "next";
String pw = "1209";

String addr = "jdbc:mysql://win.nhnnext.net/mydb";
String user = "db_user";
String pw = "1234";


#################
#### 구현 완료 ####
#################
# 1. 회원 가입
# 사용법
SET @result = NULL;
CALL sp_enterance('아이디', '유저명', '패스워드', @result);

SELECT @result;
# -> 0이면 입력 성공 or 실패


#################
#### 구현 완료 ####
#################
# 2. 로그인
# 사용법
SET @result = NULL;
CALL sp_login('아이디', '패스워드', @result);

SELECT @result;
# -> 0이면 없는 아이디 or -1이면 잘못 된 패스워드 or -2이면 블록 유저 or 정상 로그인 시 받아온 유저인덱스


#################
#### 구현 완료 ####
#################
# 3. 문서 작성
# 사용법
CALL sp_write(유저인덱스, '글제목', '컨텐츠', '카테고리');

# 참고 1. 로그인 결과 받아온 유저 인덱스를 세션 저장 한 후 여기에 입력
# 참고 2. 문서 편집 시 카테고리 리스트를 얻어온 후에 가능한 카테고리를 입력한다.


#################
#### 구현 완료 ####
#################
# 4. 문서 조회
# 사용법
SET @result = NULL;
CALL sp_read('글제목', @result);

SELECT @result;
# -> 0이면 문서를 찾을 수 없다. -> 문서 작성 페이지로
# -> 0이 아니면 SELECT 결과로 컨텐츠가 나옴
# -> 음수면 수정 불가 문서


#################
#### 구현 완료 ####
#################
# 5. 문서 수정
# 사용법
CALL sp_update(유저인덱스, '글제목', '컨텐츠');

# 글제목은 수정 불가능하도록 만들어야 함


#################
#### 구현 완료 ####
#################
# 6. 이력 조회
# 사용법
CALL sp_history(이력순서, '글제목');

# 이력 순서에 0일 경우 모든 이력 조회, 아닐 경우 해당 이력 정보 조회


#################
#### 구현 완료 ####
#################
# 7. 문서 잠금
# 사용법
CALL sp_lock(유저인덱스, '글제목', 잠금코드);

# 잠금 코드 0 : 잠금 아님


#################
#### 구현 완료 ####
#################
# 8. 문서 삭제
# 사용법
CALL sp_delete(유저인덱스, '글제목');


#################
#### 구현 완료 ####
#################
# 9. 사용자 블록
# 사용법
CALL sp_block(유저인덱스, '블록대상ID');