-- WARNING: This schema is for context only and is not meant to be run.
-- Table order and constraints may not be valid for execution.

CREATE TABLE public.ia_config (
  id integer NOT NULL DEFAULT nextval('ia_config_id_seq'::regclass),
  ia_id integer NOT NULL,
  channel character varying NOT NULL,
  ai_api character varying NOT NULL,
  encrypted_credentials character varying NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  probabilidade_audio integer DEFAULT 0,
  audio_config text,
  CONSTRAINT ia_config_pkey PRIMARY KEY (id),
  CONSTRAINT ia_config_ia_id_fkey FOREIGN KEY (ia_id) REFERENCES public.ias(id)
);
CREATE TABLE public.ias (
  id integer NOT NULL DEFAULT nextval('ias_id_seq'::regclass),
  name character varying NOT NULL UNIQUE,
  phone_number character varying NOT NULL UNIQUE,
  status boolean NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  token_ia text,
  user_id bigint,
  CONSTRAINT ias_pkey PRIMARY KEY (id),
  CONSTRAINT ias_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.leads (
  id integer NOT NULL DEFAULT nextval('leads_id_seq'::regclass),
  ia_id integer NOT NULL,
  name character varying,
  phone text,
  
  resume character varying,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  unique_token text,
  bloqueado boolean NOT NULL DEFAULT false,
  CONSTRAINT leads_pkey PRIMARY KEY (id),
  CONSTRAINT leads_ia_id_fkey FOREIGN KEY (ia_id) REFERENCES public.ias(id)
);
CREATE TABLE public.prompts (
  id integer NOT NULL DEFAULT nextval('prompts_id_seq'::regclass),
  ia_id integer NOT NULL,
  prompt_text character varying NOT NULL,
  is_active boolean NOT NULL,
  created_at timestamp with time zone DEFAULT now(),
  updated_at timestamp with time zone DEFAULT now(),
  user_id bigint,
  CONSTRAINT prompts_pkey PRIMARY KEY (id),
  CONSTRAINT prompts_ia_id_fkey FOREIGN KEY (ia_id) REFERENCES public.ias(id),
  CONSTRAINT prompts_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id)
);
CREATE TABLE public.users (
  id bigint GENERATED ALWAYS AS IDENTITY NOT NULL,
  name text NOT NULL,
  lastname text,
  email text NOT NULL,
  photo_url text,
  phone text,
  password text NOT NULL,
  created_at timestamp with time zone NOT NULL DEFAULT now(),
  updated_at timestamp with time zone NOT NULL DEFAULT now(),
  CONSTRAINT users_pkey PRIMARY KEY (id)
);


conect database supabase
NEXT_PUBLIC_SUPABASE_URL=https://gdtqbbwoxjdzkfpgezin.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImdkdHFiYndveGpkemtmcGdlemluIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDQ5MTg1MjQsImV4cCI6MjA2MDQ5NDUyNH0.TAi3z8DIuHeeokHIFf4A9WBKY9I3fZ8Bwh-W8fpAdHo