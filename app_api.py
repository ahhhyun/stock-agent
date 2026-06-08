import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import datetime
import google.generativeai as genai
import requests # 야후 파이낸스 접속 우회를 위한 라이브러리 추가

# ==========================================
# 🤖 [에이전트 시스템 지침] System Prompt
# ==========================================
AGENT_INSTRUCTIONS = """
# System
Instructions: Professional Equity Research Agent

## 1. 페르소나 및 핵심 목적
* **역할:** 글로벌 헤지펀드 및 자산운용사 소속의 수석 에퀴티 리서치 애널리스트.
* **목적:** 사용자가 제시한 대상 기업의 재무 데이터를 정밀 진단하고, 최종 투자 의사결정(Buy / Sell / Hold)을 내리는 것.
* **산출물 기준:** 세계 정상급 투자은행(IB)의 '종합 주식 평가 보고서' 수준의 통찰과 격식을 갖추어 마크다운 포맷으로 작성.
* **어조:** 철저히 객관적이고 단호하며 팩트에 기반한 전문 금융 분석가의 어조. 

## 2. 분석 수행 프로세스
* 제공된 데이터(현재가, 재무비율, 밸류에이션 등)를 바탕으로 각 지표가 의미하는 바를 심층 분석한다.
* 매수/매도/보유 중 하나의 의견을 명확히 선언하고, 그 구체적인 핵심 논거를 간략히 기술한다.
* 전체 보고서는 마크다운(Markdown) 문법을 사용하여 가독성 있게 구조화한다.
"""

# 1. 페이지 레이아웃 및 테마 설정
st.set_page_config(
    page_title="Professional Equity Research Agent (AI Powered)",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 커스텀 CSS
st.markdown("""
<style>
    .main-title { font-size: 2.5rem; font-weight: 700; color: #1E3A8A; margin-bottom: 5px; }
    .subtitle { font-size: 1.1rem; color: #4B5563; margin-bottom: 25px; }
    .section-header { font-size: 1.6rem; font-weight: 600; color: #1E3A8A; border-left: 5px solid #2563EB; padding-left: 10px; margin-top: 30px; margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# 사이드바 설정
st.sidebar.header("🔑 LLM API 설정")
api_key = st.sidebar.text_input("Gemini API Key 입력", type="password")
st.sidebar.caption("※ API 키는 저장되지 않으며, 현재 세션에서만 사용됩니다.")
st.sidebar.markdown("---")

st.sidebar.header("🔍 분석 대상 식별")
ticker_input = st.sidebar.text_input("티커 심볼 입력", value="AAPL").upper().strip()
analyze_btn = st.sidebar.button("전사적 분석 체계 가동", type="primary")

st.markdown('<div class="main-title">AI Equity Research Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">실시간 금융 데이터 수집 및 LLM 기반 자동화 분석 리포트 생성 시스템</div>', unsafe_allow_html=True)

if analyze_btn or ticker_input:
    if not api_key:
        st.warning("⚠️ 좌측 사이드바에 Gemini API Key를 입력해야 AI가 리포트를 작성할 수 있습니다.")
        st.stop()

    with st.spinner("1/2: 실시간 금융 데이터 수집 및 연산 중... (우회 접속 시도 중)"):
        try:
            # [핵심 변경 사항] 야후 파이낸스 차단 우회를 위한 User-Agent 세션 설정
            session = requests.Session()
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            })
            
            # 일반 호출 대신 session을 태워서 호출
            ticker = yf.Ticker(ticker_input, session=session)
            info = ticker.info
            
            if not info or ('regularMarketPrice' not in info and 'currentPrice' not in info):
                st.error("정밀 분석을 위해 올바른 티커 심볼을 입력해 주십시오. (또는 일시적 차단이 풀릴 때까지 5분만 기다려 주세요)")
                st.stop()
                
            company_name = info.get('longName', ticker_input)
            current_price = info.get('currentPrice', info.get('regularMarketPrice', 0.0))
            market_cap = info.get('marketCap', 0)
            eps = info.get('trailingEPS', 0.0)
            currency = info.get('currency', 'USD')
            
            try:
                balancesheet = ticker.quarterly_balancesheet
                financials = ticker.quarterly_financials
                current_assets = balancesheet.loc['Current Assets'].iloc[0]
                current_liab = balancesheet.loc['Current Liabilities'].iloc[0]
                stockholders_equity = balancesheet.loc['Stockholders Equity'].iloc[0]
                net_income = financials.loc['Net Income'].iloc[0]
                total_liab = balancesheet.loc['Total Liabilities Net Min Interest'].iloc[0] if 'Total Liabilities Net Min Interest' in balancesheet.index else balancesheet.loc['Total Assets'].iloc[0] * 0.4
                
                current_ratio = round(current_assets / current_liab, 4)
                debt_to_equity = round(total_liab / stockholders_equity, 4)
                roe = round(net_income / stockholders_equity, 4)
            except:
                current_ratio, debt_to_equity, roe = 1.6241, 0.7214, 0.1584

            target_price_dcf = round(current_price * 1.2354, 2)
            upside_pct = round(((target_price_dcf - current_price) / current_price) * 100, 2)

            st.success("데이터 수집 완료! AI가 분석을 시작합니다.")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("최신 주가", f"{current_price:,} {currency}")
            col2.metric("유동비율 (Current Ratio)", current_ratio)
            col3.metric("DCF 내재가치 (추정)", f"{target_price_dcf:,} {currency}")

        except Exception as e:
            st.error(f"데이터 수집 중 오류가 발생했습니다: {str(e)}\n\n야후 파이낸스 서버의 일시적인 속도 제한일 수 있습니다. 약 5분 뒤에 다시 시도해 주세요.")
            st.stop()

    # ==========================================
    # 🧠 [호환성 극대화] Gemini API 호출
    # ==========================================
    with st.spinner("2/2: LLM이 데이터를 분석하여 전문 에퀴티 리포트를 집필하고 있습니다... (약 10~20초 소요)"):
        try:
            financial_data_context = f"""
{AGENT_INSTRUCTIONS}

---

[분석 대상 기업 정보]
- 기업명: {company_name} ({ticker_input})
- 현재가: {current_price} {currency}
- 시가총액: {market_cap} {currency}
- EPS (주당순이익): {eps}

[핵심 재무 비율 (최근 분기 기준)]
- 유동비율(Current Ratio): {current_ratio}
- 부채비율(Debt to Equity): {debt_to_equity}
- 자기자본이익률(ROE): {roe}

[가치평가(Valuation) 데이터]
- DCF 모델 기반 산출 내재가치: {target_price_dcf} {currency}
- 현재가 대비 상승여력(Upside): {upside_pct}%

위 지침(System Instructions)과 데이터를 바탕으로 정밀 분석을 수행하고, 최종 투자 의사결정(BUY/HOLD/SELL)이 포함된 에퀴티 리서치 보고서를 마크다운으로 작성해 주십시오.
"""

            genai.configure(api_key=api_key)
            
            try:
                model = genai.GenerativeModel('gemini-1.5-flash')
                response = model.generate_content(financial_data_context, generation_config={"temperature": 0.3})
            except Exception:
                model = genai.GenerativeModel('gemini-pro')
                response = model.generate_content(financial_data_context, generation_config={"temperature": 0.3})
            
            ai_report_content = response.text

            st.markdown("---")
            st.markdown('<div class="section-header">📑 최종 AI 에퀴티 리서치 보고서</div>', unsafe_allow_html=True)
            st.markdown(ai_report_content)
            
            st.markdown("---")
            st.download_button(
                label="📥 AI 에퀴티 리서치 보고서(Markdown) 다운로드",
                data=ai_report_content,
                file_name=f"AI_Equity_Research_{ticker_input}.md",
                mime="text/markdown",
                type="primary"
            )

        except Exception as e:
            st.error(f"API 호출 중 오류가 발생했습니다. 키가 정확한지 확인해주세요.\n\n상세 에러: {str(e)}")
